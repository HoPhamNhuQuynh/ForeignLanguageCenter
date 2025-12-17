from flask_mail import Message
from foreignlanguage import mail, app


def send_register_success_email(to_email, name, class_name):
    msg = Message(
        subject="Thông báo đăng ký khóa học tại trung tâm ngoại ngữ ANQUINKO",
        recipients=[to_email]
    )

    msg.body = f"""
        Xin chào {name},
        
        Bạn đã đăng ký thành công lớp {class_name}.
        Cảm ơn bạn đã tin tưởng trung tâm.
    """

    mail.send(msg)

if __name__ == '__main__':
    with app.app_context():
        send_register_success_email(
            "quinhquinhk5@gmail.com",
            "Test User",
            "IELTS 6.5"
        )
