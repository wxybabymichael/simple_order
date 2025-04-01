from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from models import User # Import User model to check uniqueness

#update 1
from wtforms import StringField, FloatField, IntegerField, SubmitField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password', message='两次输入的密码必须一致')])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被使用，请选择其他用户名。')

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class ProfileUpdateForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    avatar = FileField('更新头像', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '只允许图片格式!')])
    current_password = PasswordField('当前密码 (如需修改密码)')
    new_password = PasswordField('新密码', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('确认新密码',
                                         validators=[Optional(), EqualTo('new_password', message='两次输入的新密码必须一致')])
    submit = SubmitField('更新个人资料')

    def __init__(self, original_username, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('该用户名已被使用，请选择其他用户名。')

    def validate_new_password(self, new_password):
        # If current_password is provided, new_password must also be provided
        if self.current_password.data and not new_password.data:
             raise ValidationError('请输入新密码。')
        # If new_password is provided, current_password must also be provided
        if new_password.data and not self.current_password.data:
            raise ValidationError('请输入当前密码以设置新密码。')

class ExcelUploadForm(FlaskForm):
    excel_file = FileField('选择 Excel 文件 (.xlsx, .xls)', validators=[
        FileRequired(message='请选择一个文件！'),
        FileAllowed(['xlsx', 'xls'], '只允许 Excel 文件！')
    ])
    submit = SubmitField('上传并处理')


# update 1
# New Form for Editing Orders
class OrderEditForm(FlaskForm):
    # Keep order_id and coupon_code non-editable, but maybe display them
    supplier_name = StringField('供应商名称', validators=[Optional(), Length(max=128)])
    customer_name = StringField('客户名称', validators=[DataRequired(), Length(max=64)])
    amount = FloatField('金额', validators=[DataRequired(), NumberRange(min=0)])
    # Use StringField for phone to avoid potential type issues if it contains non-digits
    phone = StringField('电话', validators=[DataRequired(), Length(min=5, max=20)])
    # Maybe allow editing status or validity? For now, keep it simple.
    # status = SelectField('状态', choices=[('已激活', '已激活'), ('已使用', '已使用'), ('已过期','已过期')], validators=[DataRequired()])
    # validity_months = IntegerField('有效期 (月)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('保存更改')