# app/marketplace/routes.py
# Author: Indrajit Ghosh
# Created On: Oct 18, 2025
# 
from flask import render_template, request, redirect, url_for, flash, session, current_app
from sqlalchemy.orm import joinedload
from app.marketplace import marketplace_bp
from app.extensions import db
from app.marketplace.models import Seller, Advertisement, Product, ProductBooking
import random, string
from scripts.send_email_client import send_email_via_hermes
from config import EmailConfig
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

# ---------- Public routes ----------
@marketplace_bp.route('/')
def index():
    return render_template('marketplace/index.html')

@marketplace_bp.route('/sellers/')
def sellers():
    # Fetch sellers with ads
    sellers = Seller.query.options(db.joinedload(Seller.ads)).order_by(Seller.created_at.desc()).all()
    return render_template('marketplace/sellers.html', sellers=sellers)


@marketplace_bp.route('/listings/')
def listings():
    seller_uuid = request.args.get('seller_uuid')  # optional query param

    query = Advertisement.query.order_by(Advertisement.created_at.desc())

    if seller_uuid:
        # Join with Seller to filter by UUID
        query = query.join(Advertisement.seller).filter(Seller.uuid == seller_uuid)

    ads = query.all()
    return render_template('marketplace/listings.html', ads=ads)

@marketplace_bp.route('/ads/<uuid>')
def view_ad(uuid):
    ad = Advertisement.query.filter_by(uuid=uuid).first_or_404()

    seller = None
    seller_id = session.get('seller_id')
    if seller_id:
        seller = Seller.query.get(seller_id)

    return render_template('marketplace/view_ad.html', ad=ad, seller=seller)


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

    # --- Email content ---
    subject = f"Verify your booking for '{product.name}'"
    html_body = f"""
    <div style="font-family:Arial, sans-serif; color:#333; line-height:1.6;">
      <h2 style="color:#0d6efd;">Slotify Marketplace</h2>

      <p>Hello,</p>
      <p>
        You have requested to book <strong>{product.name}</strong> 
        for ₹{product.price_inr:.2f}.
      </p>

      <p>Your One-Time Password (OTP) for verification is:</p>
      <h2 style="background:#f8f9fa; padding:12px 20px; display:inline-block; border-radius:8px; color:#000; letter-spacing:3px; border:1px solid #ddd;">
        {otp}
      </h2>

      <p style="margin-top:12px;">
        Please enter this OTP on the verification page to confirm your booking.
      </p>

      <p style="font-size:0.9em; color:#777;">
        If you did not request this booking, you can safely ignore this email.
      </p>

      <hr style="margin-top:20px; margin-bottom:10px;">

      <p style="font-size:0.9em; color:#555;">
    Kind regards,<br>
    <strong>Indrajit</strong><br>
    Owner, <a href="https://slotify.pythonanywhere.com/marketplace" target="_blank" style="color:#0d6efd;">Slotify Marketplace</a><br>
    My personal webpage is 
    <a href="https://indrajitghosh.onrender.com" target="_blank" style="color:#0d6efd; text-decoration:none;">here</a>.<br>
    Bangalore, India
  </p>
  </div>
    """

    # --- Send email via Hermes ---
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

            # --- Send email to the seller ---
            product = booking.product
            ad = product.advertisement
            seller = ad.seller

            ad_link = url_for('marketplace.view_ad', uuid=ad.uuid, _external=True)

            subject = f"Order Notification: {product.name} has been booked"
            html_body = f"""
            <div style="font-family:Arial, sans-serif; color:#333; line-height:1.6;">
              <h2 style="color:#0d6efd;">Slotify Marketplace</h2>

              <p>Dear {seller.name},</p>

              <p>
                A buyer has successfully verified their booking for your product 
                <strong>{product.name}</strong> (₹{product.price_inr:.2f}).
              </p>

              <h4 style="margin-top:12px;">Buyer Details:</h4>
              <ul style="margin:0; padding-left:20px;">
                <li><strong>Email:</strong> {booking.buyer_email}</li>
              </ul>

              <p style="margin-top:12px;">
                You can review the advertisement and booking details here:
                <br>
                <a href="{ad_link}" target="_blank" style="color:#0d6efd; text-decoration:none;">
                  🔗 View Advertisement
                </a>
              </p>

              <p style="font-size:0.95em; color:#555;">
                Please contact the buyer directly to coordinate delivery and payment, if applicable.
              </p>

              <hr style="margin-top:20px; margin-bottom:10px;">

<p style="font-size:0.9em; color:#555;">
    Kind regards,<br>
    <strong>Indrajit</strong><br>
    Owner, <a href="https://slotify.pythonanywhere.com/marketplace" target="_blank" style="color:#0d6efd;">Slotify Marketplace</a><br>
    My personal webpage is 
    <a href="https://indrajitghosh.onrender.com" target="_blank" style="color:#0d6efd; text-decoration:none;">here</a>.<br>
    Bangalore, India
  </p>
            </div>
            """

            try:
                response = send_email_via_hermes(
                    to=seller.email,
                    subject=subject,
                    email_html_text=html_body,
                    api_key=EmailConfig.HERMES_API_KEY,
                    bot_id=EmailConfig.HERMES_EMAILBOT_ID,
                    api_url=f"{EmailConfig.HERMES_BASE_URL}/api/v1/send-email",
                    from_name="Slotify Marketplace"
                )

                if response.get("success"):
                    flash('Booking verified successfully! Seller has been notified.', 'success')
                else:
                    flash('Booking verified, but failed to notify seller.', 'warning')

            except Exception as e:
                print(f"Error sending seller email: {e}")
                flash('Booking verified, but could not send seller notification.', 'danger')

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
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('marketplace.seller_register'))

        # Check if email already registered
        if Seller.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return redirect(url_for('marketplace.seller_register'))

        # Create and save new seller
        seller = Seller(name=name, email=email)
        seller.set_password(password)
        db.session.add(seller)
        db.session.commit()

        flash('Seller registered successfully! You can now log in.', 'success')
        return redirect(url_for('marketplace.seller_login'))

    return render_template('marketplace/seller_register.html')


@marketplace_bp.route('/sellers/forgot_password/', methods=['GET', 'POST'])
def seller_forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        seller = Seller.query.filter_by(email=email).first()

        if not seller:
            flash('No account found with that email.', 'warning')
            return redirect(url_for('marketplace.seller_forgot_password'))

        token = get_serializer().dumps(email, salt='password-reset-salt')
        reset_url = url_for('marketplace.seller_reset_password', token=token, _external=True)

        html_body = f"""
        <p>Hi {seller.name},</p>
        <p>You requested to reset your password. Click the link below:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>This link will expire in 1 hour.</p>
        """

        send_email_via_hermes(
            to=email,
            subject="Password Reset - Slotify Marketplace",
            email_html_text=html_body,
            api_key=EmailConfig.HERMES_API_KEY,
            bot_id=EmailConfig.HERMES_EMAILBOT_ID,
            api_url=EmailConfig.HERMES_BASE_URL + "/api/v1/send-email",
            from_name="Slotify Marketplace"
        )

        flash('A password reset link has been sent to your email.', 'info')
        return redirect(url_for('marketplace.seller_login'))

    return render_template('marketplace/seller_forgot_password.html')


@marketplace_bp.route('/sellers/reset_password/<token>/', methods=['GET', 'POST'])
def seller_reset_password(token):
    try:
        email = get_serializer().loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('marketplace.seller_forgot_password'))
    except BadSignature:
        flash('Invalid or tampered reset link.', 'danger')
        return redirect(url_for('marketplace.seller_forgot_password'))

    seller = Seller.query.filter_by(email=email).first_or_404()

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('marketplace.seller_reset_password', token=token))

        seller.set_password(password)
        db.session.commit()

        flash('Your password has been updated successfully.', 'success')
        return redirect(url_for('marketplace.seller_login'))

    return render_template('marketplace/seller_reset_password.html', email=email)


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
    image_url = request.form.get('image_url', '')

    product = Product(
        name=name,
        price_inr=price_inr,
        description=description,
        image_url=image_url,
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
        product.image_url = request.form.get('image_url', None)

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('marketplace.view_ad', uuid=product.advertisement.uuid))

    # For GET: render the edit form prefilled
    return render_template('marketplace/edit_product.html', product=product)

@marketplace_bp.route('/delete_product/<product_uuid>', methods=['POST'])
def delete_product(product_uuid):
    product = Product.query.options(joinedload(Product.advertisement)).filter_by(uuid=product_uuid).first_or_404()
    seller_id = session.get('seller_id')

    # Ensure the logged-in seller owns this product
    if not seller_id or product.advertisement.seller_id != seller_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('marketplace.view_ad', uuid=product.advertisement.uuid))

    ad_uuid = product.advertisement.uuid

    # Delete the product
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully.', 'success')
    return redirect(url_for('marketplace.view_ad', uuid=ad_uuid))



@marketplace_bp.route('/ads/delete/<uuid>', methods=['POST'])
def delete_ad(uuid):
    ad = Advertisement.query.options(joinedload(Advertisement.seller)).filter_by(uuid=uuid).first_or_404()

    seller_uuid = ad.seller.uuid
    db.session.delete(ad)
    db.session.commit()

    flash('Advertisement deleted successfully.', 'success')
    return redirect(url_for('marketplace.seller_dashboard', seller_uuid=seller_uuid))

@marketplace_bp.route("/product/<product_uuid>/toggle-delivery", methods=["POST"])
def toggle_delivery_status(product_uuid):
    product = Product.query.filter_by(uuid=product_uuid).first_or_404()

    # Only the seller of this product can change delivery status
    if product.advertisement.seller_id != session.get('seller_id'):
        abort(403)

    product.is_delivered = not product.is_delivered
    db.session.commit()

    # Send email to buyer if delivered
    if product.is_delivered:
        # Get all verified bookings for this product
        bookings = ProductBooking.query.filter_by(product_id=product.id, is_verified=True).all()
        for booking in bookings:
            buyer_email = booking.buyer_email
            ad_link = url_for('marketplace.view_ad', uuid=product.advertisement.uuid, _external=True)

            subject = f"Your order '{product.name}' has been delivered!"
            html_body = f"""
            <div style="font-family:Arial, sans-serif; color:#333; line-height:1.6;">
              <h2 style="color:#0d6efd;">Slotify Marketplace</h2>

              <p>Hello,</p>

              <p>
                Good news! Your order for <strong>{product.name}</strong> (₹{product.price_inr:.2f}) has been marked as <strong>Delivered</strong> by the seller.
              </p>

              <p>You can view your order details here: 
                <a href="{ad_link}" target="_blank" style="color:#0d6efd; text-decoration:none;">
                  🔗 View Advertisement
                </a>
              </p>

              <hr style="margin-top:20px; margin-bottom:10px;">

              <p style="font-size:0.9em; color:#555;">
                Kind regards,<br>
                <strong>Indrajit</strong><br>
                Owner, <a href="https://slotify.pythonanywhere.com/marketplace" target="_blank" style="color:#0d6efd;">Slotify Marketplace</a><br>
                My personal webpage is <a href="https://indrajitghosh.onrender.com" target="_blank" style="color:#0d6efd; text-decoration:none;">here</a>.<br>
                Bangalore, India
              </p>
            </div>
            """

            try:
                response = send_email_via_hermes(
                    to=buyer_email,
                    subject=subject,
                    email_html_text=html_body,
                    api_key=EmailConfig.HERMES_API_KEY,
                    bot_id=EmailConfig.HERMES_EMAILBOT_ID,
                    api_url=f"{EmailConfig.HERMES_BASE_URL}/api/v1/send-email",
                    from_name="Slotify Marketplace"
                )
                if not response.get("success"):
                    print(f"Failed to send delivery email to {buyer_email}")
            except Exception as e:
                print(f"Error sending delivery email to {buyer_email}: {e}")

    flash(
        f"Delivery status changed to {'Delivered' if product.is_delivered else 'Not Delivered'}.",
        "info"
    )
    return redirect(request.referrer or url_for("marketplace.listings"))
