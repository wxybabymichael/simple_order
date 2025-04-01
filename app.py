import os
import random
import string
import pandas as pd
from datetime import datetime
# Import 'or_' from sqlalchemy for complex OR queries
from sqlalchemy import or_
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
# Import WTForms csrf protection
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User, Order
from forms import RegistrationForm, LoginForm, ProfileUpdateForm, ExcelUploadForm, OrderEditForm

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to 'login' view if user is not logged in
login_manager.login_message = '请先登录以访问此页面。'
login_manager.login_message_category = 'info'

# Enable CSRF protection globally (Ensure SECRET_KEY is set in Config)
csrf = CSRFProtect(app)

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    """Loads user object from user ID stored in the session."""
    return User.query.get(int(user_id))

# --- Helper Functions ---

def generate_random_string(length):
    """Generates a random string of lowercase letters and digits."""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choices(characters, k=length))

def generate_order_id():
    """Generates a unique Order ID (NMCFxxxx)."""
    while True:
        order_id = 'NMCF' + generate_random_string(4)
        if not Order.query.filter_by(order_id=order_id).first():
            return order_id

def generate_coupon_code():
    """Generates a unique Coupon Code (CXxxxxxxx)."""
    while True:
        coupon_code = 'CX' + generate_random_string(7)
        if not Order.query.filter_by(coupon_code=coupon_code).first():
            return coupon_code

def allowed_file(filename, allowed_extensions):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# --- Routes ---

@app.route('/')
@app.route('/index')
@login_required
def index():
    """Displays the main page with orders, search, and pagination.
       Hides supplier column if supplier name is searched (even with customer name)."""
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Records per page
    # Get search terms from URL query parameters
    supplier_query = request.args.get('supplier_query', '').strip()
    customer_query_string = request.args.get('customer_query', '').strip()

    # Start with a base query for all orders
    query = Order.query

    # Initialize flags/variables for template rendering
    hide_supplier_column = False
    searched_supplier_name = None

    # --- Updated Search Logic ---

    # 1. Handle Supplier Search & Column Hiding Condition
    #    If supplier_query has *any* value, filter by it, set flag to hide the column,
    #    and store the searched name for display.
    if supplier_query:
        query = query.filter(Order.supplier_name.ilike(f'%{supplier_query}%')) # Apply filter
        hide_supplier_column = True  # Set flag to hide column
        searched_supplier_name = supplier_query # Store name for display

    # 2. Handle Customer Search (potentially multiple names)
    #    This filter is applied *in addition* to the supplier filter if both are present.
    if customer_query_string:
        # Normalize delimiters (commas, semicolons, etc.) to spaces
        normalized_query = customer_query_string.replace(',', ' ').replace(';', ' ')
        # Add more .replace() if other delimiters like '|' are expected

        # Split by space and clean up terms (remove empty strings)
        customer_names = [name.strip() for name in normalized_query.split(' ') if name.strip()]

        # If valid customer names were extracted, build and apply the OR condition
        if customer_names:
            # Create a list of individual ILIKE conditions
            conditions = [Order.customer_name.ilike(f'%{name}%') for name in customer_names]
            # Apply the OR conditions to the query (which might already be filtered by supplier)
            query = query.filter(or_(*conditions)) # Use * to unpack list arguments

    # --- End Search Logic ---

    # Apply ordering and pagination *after* all filtering is done
    orders_pagination = query.order_by(Order.upload_timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    orders = orders_pagination.items # Get the records for the current page

    # Calculate display information (e.g., "Showing 1 to 10 of 50 records")
    total_records = orders_pagination.total
    start_record = (page - 1) * per_page + 1 if total_records > 0 else 0
    end_record = min(start_record + per_page - 1, total_records)
    display_info = f"显示第 {start_record} 到第 {end_record} 条记录，总共 {total_records} 条记录"

    # Render the main index template, passing all necessary data and flags
    return render_template('index.html', title='客户订单管理系统',
                           orders=orders,
                           pagination=orders_pagination,
                           display_info=display_info,
                           hide_supplier_column=hide_supplier_column, # Template uses this flag
                           searched_supplier_name=searched_supplier_name, # Template uses this value
                           supplier_query=supplier_query, # To pre-fill search boxes
                           customer_query=customer_query_string) # Pass original string back

# --- NEW Batch Delete Route ---
@app.route('/orders/batch_delete', methods=['POST'])
@login_required
def batch_delete_orders():
    """Handles deletion of multiple orders based on selected checkboxes."""
    # Get list of IDs from checkboxes named 'order_ids'
    order_ids_to_delete = request.form.getlist('order_ids')

    if not order_ids_to_delete:
        flash('没有选择任何记录进行删除。', 'warning')
        return redirect(url_for('index'))

    try:
        # Ensure all submitted IDs are valid integers
        valid_ids = [int(id_str) for id_str in order_ids_to_delete]
    except ValueError:
        flash('提交的记录 ID 包含无效值。', 'danger')
        return redirect(url_for('index'))

    deleted_count = 0
    try:
        # Perform bulk delete efficiently
        num_deleted = Order.query.filter(Order.id.in_(valid_ids)).delete(synchronize_session='fetch')
        db.session.commit() # Commit the transaction
        deleted_count = num_deleted if num_deleted is not None else 0 # Get the count of deleted rows

        if deleted_count > 0:
             flash(f'成功删除 {deleted_count} 条记录。', 'success')
        else:
             # This might happen if the records were already deleted between page load and submit
             flash('没有记录被删除（可能已被删除或 ID 无效）。', 'info')

    except Exception as e:
        db.session.rollback() # Rollback transaction on error
        flash(f'批量删除时发生错误: {e}', 'danger')
        app.logger.error(f"Batch delete error for IDs {valid_ids}: {e}")

    return redirect(url_for('index')) # Redirect back to the main list page

# --- User Authentication Routes (Unchanged) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, avatar='default_avatar.png'); user.set_password(form.password.data)
        db.session.add(user)
        try: db.session.commit(); flash('恭喜，您已成功注册！现在可以登录了。', 'success'); return redirect(url_for('login'))
        except Exception as e: db.session.rollback(); flash(f'注册时出错: {e}', 'danger'); app.logger.error(f"Registration error: {e}")
    return render_template('register.html', title='注册', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data): flash('无效的用户名或密码。', 'danger'); return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data); flash(f'欢迎回来, {user.username}!', 'success')
        next_page = request.args.get('next');
        if not next_page or not next_page.startswith('/'): next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='登录', form=form)

@app.route('/logout')
@login_required
def logout(): logout_user(); flash('您已成功登出。', 'info'); return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileUpdateForm(current_user.username)
    if form.validate_on_submit():
        updated = False
        if form.username.data != current_user.username: current_user.username = form.username.data; flash('用户名已更新。', 'success'); updated = True
        if form.current_password.data and form.new_password.data:
            if current_user.check_password(form.current_password.data): current_user.set_password(form.new_password.data); flash('密码已成功修改。', 'success'); updated = True
            else: flash('当前密码不正确，密码未修改。', 'danger'); db.session.rollback(); avatar_url = url_for('static', filename=f'uploads/avatars/{current_user.avatar}'); return render_template('profile.html', title='个人资料', form=form, avatar_url=avatar_url)
        if form.avatar.data:
            file = form.avatar.data
            if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS_AVATAR']):
                _, f_ext = os.path.splitext(file.filename); filename = secure_filename(f"{current_user.id}_{int(datetime.utcnow().timestamp())}{f_ext}"); filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if current_user.avatar and current_user.avatar != 'default_avatar.png':
                     old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.avatar)
                     if os.path.exists(old_avatar_path):
                         try: os.remove(old_avatar_path)
                         except OSError as e: app.logger.error(f"Error removing old avatar {old_avatar_path}: {e}")
                try: file.save(filepath); current_user.avatar = filename; flash('头像已更新。', 'success'); updated = True
                except Exception as e: flash(f'保存头像时出错: {e}', 'danger'); app.logger.error(f"Avatar save error: {e}")
            elif file.filename != '': flash('无效的头像文件格式。只允许 png, jpg, jpeg, gif。', 'warning')
        if updated:
            try: db.session.commit()
            except Exception as e: db.session.rollback(); flash(f'更新个人资料时出错: {e}', 'danger'); app.logger.error(f"Profile update commit error: {e}")
        return redirect(url_for('profile'))
    elif request.method == 'GET': form.username.data = current_user.username
    avatar_url = url_for('static', filename=f'uploads/avatars/{current_user.avatar}')
    return render_template('profile.html', title='个人资料', form=form, avatar_url=avatar_url)

# --- Data Management Routes (Upload/Edit remain the same) ---
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handles the upload and processing of Excel files."""
    form = ExcelUploadForm()
    if form.validate_on_submit():
        file = form.excel_file.data
        if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS_EXCEL']):
            try:
                # Define expected Excel columns and their corresponding model attributes
                expected_columns = {
                    '供应商名称': 'supplier_name', '客户名称': 'customer_name',
                    '金额': 'amount', '发放时间': 'issue_time', '电话': 'phone'
                }
                df = pd.read_excel(file, engine='openpyxl') # Read the Excel file

                # Rename columns found in the DataFrame according to the mapping
                rename_map = {k: v for k, v in expected_columns.items() if k in df.columns}
                df.rename(columns=rename_map, inplace=True)

                # Initialize counters and lists for processing results
                processed_count = 0; skipped_count = 0; errors = []; new_orders = []

                # Check if essential columns are present after renaming
                required_cols_present = all(col in df.columns for col in ['customer_name', 'amount', 'phone'])
                if not required_cols_present:
                     flash('上传的文件缺少必要的列 (客户名称, 金额, 电话)。请检查文件标题行。', 'danger')
                     return render_template('upload.html', title='上传 Excel 文件', form=form)

                # Process each row in the DataFrame
                for index, row in df.iterrows():
                    row_num = index + 2 # For user-friendly error messages (Excel rows are 1-based, plus header)

                    # Validate essential data presence for the current row
                    if not all(pd.notna(row.get(col)) for col in ['customer_name', 'amount', 'phone']):
                        errors.append(f"第 {row_num} 行：缺少必要数据 (客户名称, 金额, 电话)，已跳过。"); skipped_count += 1; continue

                    # Parse '发放时间', default to now() if invalid or missing
                    issue_time_val = row.get('issue_time'); issue_time_dt = datetime.utcnow()
                    try:
                        parsed_dt = pd.to_datetime(issue_time_val) # Pandas handles many formats
                        if not pd.isna(parsed_dt): issue_time_dt = parsed_dt # Use parsed date if valid
                        else: raise ValueError("Parsed date is NaT") # Treat NaT as invalid
                    except (ValueError, TypeError, Exception):
                        # Warn only if a value was present but couldn't be parsed
                        if issue_time_val is not None: errors.append(f"第 {row_num} 行：发放时间 '{issue_time_val}' 无效或格式错误，已使用当前时间。")

                    # Attempt to create the Order object
                    try:
                        new_order = Order(
                            order_id=generate_order_id(),
                            supplier_name=str(row.get('supplier_name', '')).strip(), # Handle optional supplier
                            customer_name=str(row['customer_name']).strip(),
                            amount=float(row['amount']), # Ensure amount is float
                            issue_time=issue_time_dt,
                            phone=str(row['phone']).strip(), # Ensure phone is string
                            coupon_code=generate_coupon_code(),
                            validity_months=12, # Fixed validity
                            status='已激活' # Fixed status
                        )
                        new_orders.append(new_order) # Add to batch list
                        processed_count += 1
                    # Handle potential data type errors during object creation
                    except (ValueError, TypeError) as data_err:
                        errors.append(f"第 {row_num} 行：数据类型转换错误 (例如金额或电话)，已跳过。错误: {data_err}"); skipped_count += 1; continue
                    # Catch any other unexpected errors for the row
                    except Exception as e:
                        errors.append(f"第 {row_num} 行：创建记录时发生未知错误，已跳过。错误: {e}"); skipped_count += 1; continue

                # Commit all successfully created orders in one transaction
                if new_orders:
                    db.session.add_all(new_orders)
                    db.session.commit()

                # Provide summary feedback
                flash(f'文件处理完成。成功添加 {processed_count} 条记录。跳过 {skipped_count} 条记录。', 'success')
                # Show specific row-level warnings/errors
                for error in errors: flash(error, 'warning')

                return redirect(url_for('index')) # Go back to the main list

            # Catch major errors during file reading or processing
            except Exception as e:
                db.session.rollback() # Rollback any partial changes
                flash(f'处理 Excel 文件时发生严重错误: {e}', 'danger')
                app.logger.error(f"Excel processing error: {e}") # Log detailed error
        else:
            # This case should be rare due to WTForms validation but serves as a safeguard
            flash('无效的文件类型或未选择文件。请上传 .xlsx 或 .xls 文件。', 'warning')

    # Render the upload page template
    return render_template('upload.html', title='上传 Excel 文件', form=form)

@app.route('/order/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    """Displays and handles editing of a specific order."""
    order = Order.query.get_or_404(order_id) # Fetch order or return 404
    form = OrderEditForm(obj=order) # Pre-populate form with order data
    if form.validate_on_submit():
        # Update order attributes from form data
        order.supplier_name = form.supplier_name.data.strip() if form.supplier_name.data else None
        order.customer_name = form.customer_name.data.strip()
        order.amount = form.amount.data
        order.phone = form.phone.data.strip()
        # Add other fields here if they become editable
        try:
            db.session.commit() # Save changes
            flash(f'订单 {order.order_id} 已成功更新！', 'success')
            return redirect(url_for('index')) # Redirect to main list
        except Exception as e:
            db.session.rollback()
            flash(f'更新订单时出错: {e}', 'danger')
            app.logger.error(f"Error updating order {order_id}: {e}")

    # Get masked values for display reference in the template
    masked_phone = order.masked_phone; masked_coupon = order.masked_coupon_code
    return render_template('edit_order.html', title=f'编辑订单 {order.order_id}', form=form, order=order,
                           masked_phone=masked_phone, masked_coupon=masked_coupon)

# --- Static file serving (for avatars - Unchanged) ---
@app.route('/static/uploads/avatars/<path:filename>')
def uploaded_avatar(filename):
    safe_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    if not safe_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])): abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Database Initialization (Unchanged) ---
def initialize_database():
     with app.app_context():
         db.create_all()
         if not User.query.first():
             try:
                 default_user = User(username='admin', avatar='default_avatar.png'); default_user.set_password('password') # CHANGE THIS!
                 db.session.add(default_user); db.session.commit()
                 print("*"*60); print("Default user 'admin' with password 'password' created."); print("IMPORTANT: Change the default password immediately via the profile page!"); print("*"*60)
             except Exception as e: db.session.rollback(); print(f"Error creating default user: {e}"); app.logger.error(f"Error creating default user: {e}")

# --- Main Execution Block ---
if __name__ == '__main__':
    initialize_database() # Ensure DB and default user exist before starting server
    app.run(debug=False, host='0.0.0.0', port=5000) # Run development server