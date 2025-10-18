# app/marketplace/routes.py
from flask import render_template, request, redirect, url_for, flash, session
from sqlalchemy.orm import joinedload
from app.marketplace import marketplace_bp
from app.extensions import db
from app.marketplace.models import Seller, Advertisement, Product, ProductBooking
import random, string
from scripts.send_email_client import send_email_via_hermes
from config import EmailConfig


# ---------- Public routes ----------
@marketplace_bp.route('/')
def index():
    return render_template('marketplace/index.html')

@marketplace_bp.route('/listings/')
def listings():
    ads = Advertisement.query.order_by(Advertisement.created_at.desc()).all()
    return render_template('marketplace/listings.html', ads=ads)

@marketplace_bp.route('/ads/<uuid>')
def view_ad(uuid):
    ad = Advertisement.query.filter_by(uuid=uuid).first_or_404()

    seller = None
    seller_id = session.get('seller_id')
    if seller_id:
        seller = Seller.query.get(seller_id)

    return render_template('marketplace/view_ad.html', ad=ad, seller=seller)


# ---------- Buyer Booking ----------
@marketplace_bp.route('/book/<product_uuid>', methods=['POST'])
def book_product(product_uuid):
    product = Product.query.filter_by(uuid=product_uuid).first_or_404()
    if product.is_sold:
        flash('Sorry, this product is already sold.', 'warning')
        return redirect(url_for('marketplace.index'))

    # Get buyer email
    email = request.form['email'].strip()
    if not email:
        flash('Please enter a valid email address.', 'danger')
        return redirect(url_for('marketplace.view_ad', uuid=product.advertisement.uuid))

    # Generate OTP
    otp = ''.join(random.choices(string.digits, k=6))

    # Create booking entry
    booking = ProductBooking(
        product_id=product.id,
        buyer_email=email,
        otp_code=otp
    )
    db.session.add(booking)
    db.session.commit()

    # Email content
    subject = f"Verify your booking for '{product.name}'"
    html_body = f"""
    <div style="font-family:Arial, sans-serif; color:#333;">
      <h2 style="color:#2a7ae2;">Slotify Marketplace</h2>
      <p>Hello,</p>
      <p>You have requested to book <strong>{product.name}</strong> (₹{product.price_inr:.2f}).</p>
      <p>Your One-Time Password (OTP) for verification is:</p>
      <h3 style="background:#f0f0f0; padding:10px; display:inline-block; border-radius:6px;">{otp}</h3>
      <p>Please enter this OTP on the verification page to confirm your booking.</p>
      <br>
      <p style="font-size:0.9em; color:#777;">If you did not request this, you can safely ignore this email.</p>
      <hr>
      <p><strong>Slotify Marketplace</strong><br>
      <a href="https://slotify.pythonanywhere.com/marketplace" target="_blank">Visit Marketplace</a></p>
    </div>
    """

    # Send email using Hermes
    try:
        response = send_email_via_hermes(
            to=email,
            subject=subject,
            email_html_text=html_body,
            api_key=EmailConfig.HERMES_API_KEY,
            bot_id=EmailConfig.HERMES_EMAILBOT_ID,
            api_url=f"{EmailConfig.HERMES_BASE_URL}/api/v1/send-email",
            from_name="Slotify Marketplace"
        )

        if response.get("success"):
            flash('OTP sent to your email. Please verify.', 'info')
        else:
            flash('Booking created, but failed to send email. Please contact support.', 'warning')

    except Exception as e:
        print(f"Error sending email: {e}")
        flash('An error occurred while sending the verification email.', 'danger')

    return redirect(url_for('marketplace.verify_booking', booking_id=booking.id))


@marketplace_bp.route('/verify_booking/<int:booking_id>', methods=['GET', 'POST'])
def verify_booking(booking_id):
    booking = ProductBooking.query.get_or_404(booking_id)
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == booking.otp_code:
            booking.is_verified = True
            booking.product.is_sold = True
            db.session.commit()
            flash('Booking verified successfully! Seller will contact you soon.', 'success')
            return redirect(url_for('marketplace.listings'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    return render_template('marketplace/verify_booking.html', booking=booking)

@marketplace_bp.route('/remove_buyer/<product_uuid>', methods=['POST'])
def remove_buyer(product_uuid):
    seller_id = session.get('seller_id')
    product = Product.query.filter_by(uuid=product_uuid).first_or_404()

    # Ensure only the seller who owns the product can remove the buyer
    if not seller_id or product.advertisement.seller_id != seller_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('marketplace.seller_dashboard', seller_uuid=session.get('seller_uuid')))

    # Find the verified booking
    verified_booking = ProductBooking.query.filter_by(product_id=product.id, is_verified=True).first()
    if verified_booking:
        db.session.delete(verified_booking)
        product.is_sold = False
        db.session.commit()
        flash('Buyer removed successfully. Product is now available for booking.', 'success')
    else:
        flash('No verified buyer to remove.', 'warning')

    return redirect(url_for('marketplace.view_ad', uuid=product.advertisement.uuid))



# ---------- Seller Authentication ----------
@marketplace_bp.route('/sellers/register/', methods=['GET', 'POST'])
def seller_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if Seller.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return redirect(url_for('marketplace.seller_register'))

        seller = Seller(name=name, email=email)
        seller.set_password(password)
        db.session.add(seller)
        db.session.commit()
        flash('Seller registered successfully! You can now log in.', 'success')
        return redirect(url_for('marketplace.seller_login'))
    return render_template('marketplace/seller_register.html')


@marketplace_bp.route('/sellers/login/', methods=['GET', 'POST'])
def seller_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        seller = Seller.query.filter_by(email=email).first()
        if seller and seller.check_password(password):
            session['seller_id'] = seller.id
            session['seller_uuid'] = seller.uuid
            flash('Login successful.', 'success')
            return redirect(url_for('marketplace.seller_dashboard', seller_uuid=seller.uuid))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('marketplace/seller_login.html')


@marketplace_bp.route('/sellers/logout/')
def seller_logout():
    session.pop('seller_id', None)
    session.pop('seller_uuid', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('marketplace.index'))


# ---------- Seller Dashboard ----------
@marketplace_bp.route('/sellers/<seller_uuid>/')
def seller_dashboard(seller_uuid):
    if session.get('seller_uuid') != seller_uuid:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('marketplace.seller_login'))
    seller = Seller.query.filter_by(uuid=seller_uuid).first_or_404()
    return render_template('marketplace/seller_dashboard.html', seller=seller)


@marketplace_bp.route('/sellers/<seller_uuid>/add_ad', methods=['POST'])
def add_ad(seller_uuid):
    if session.get('seller_uuid') != seller_uuid:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('marketplace.seller_login'))

    seller = Seller.query.filter_by(uuid=seller_uuid).first_or_404()
    title = request.form['title']
    desc = request.form.get('description')
    ad = Advertisement(title=title, description=desc, seller=seller)
    db.session.add(ad)
    db.session.commit()
    flash('Advertisement added successfully.', 'success')
    return redirect(url_for('marketplace.seller_dashboard', seller_uuid=seller_uuid))

@marketplace_bp.route('/ads/edit/<ad_uuid>', methods=['GET', 'POST'])
def edit_ad(ad_uuid):
    ad = Advertisement.query.filter_by(uuid=ad_uuid).first_or_404()
    seller_uuid = session.get('seller_uuid')

    # Check ownership
    if not seller_uuid or ad.seller.uuid != seller_uuid:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('marketplace.seller_login'))

    if request.method == 'POST':
        ad.title = request.form['title']
        ad.description = request.form.get('description', '')
        db.session.commit()
        flash('Advertisement updated successfully.', 'success')
        return redirect(url_for('marketplace.seller_dashboard', seller_uuid=seller_uuid))

    # If GET, render edit form
    return render_template('marketplace/edit_ad.html', ad=ad)


@marketplace_bp.route('/add_product/<uuid>', methods=['POST'])
def add_product(uuid):
    ad = Advertisement.query.filter_by(uuid=uuid).first_or_404()
    seller_id = session.get('seller_id')

    if not seller_id or ad.seller_id != seller_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('marketplace.view_ad', uuid=uuid))

    name = request.form['name']
    price_inr = float(request.form['price_inr'])
    description = request.form.get('description', '')

    product = Product(
        name=name,
        price_inr=price_inr,
        description=description,
        ad_id=ad.id
    )
    db.session.add(product)
    db.session.commit()

    flash('Product added successfully!', 'success')
    return redirect(url_for('marketplace.view_ad', uuid=uuid))

@marketplace_bp.route('/edit_product/<product_uuid>', methods=['GET', 'POST'])
def edit_product(product_uuid):
    product = Product.query.options(joinedload(Product.advertisement)).filter_by(uuid=product_uuid).first_or_404()
    seller_id = session.get('seller_id')

    # Ensure the logged-in seller owns this product
    if not seller_id or product.advertisement.seller_id != seller_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('marketplace.view_ad', uuid=product.advertisement.uuid))

    if request.method == 'POST':
        product.name = request.form['name']
        product.price_inr = float(request.form['price_inr'])
        product.description = request.form.get('description', '')

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('marketplace.view_ad', uuid=product.advertisement.uuid))

    # For GET: render the edit form prefilled
    return render_template('marketplace/edit_product.html', product=product)


@marketplace_bp.route('/ads/delete/<uuid>', methods=['POST'])
def delete_ad(uuid):
    ad = Advertisement.query.options(joinedload(Advertisement.seller)).filter_by(uuid=uuid).first_or_404()

    seller_uuid = ad.seller.uuid
    db.session.delete(ad)
    db.session.commit()

    flash('Advertisement deleted successfully.', 'success')
    return redirect(url_for('marketplace.seller_dashboard', seller_uuid=seller_uuid))
