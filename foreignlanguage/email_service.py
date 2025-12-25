from flask_mail import Message
from foreignlanguage import mail, app


def send_register_success_email(to_email, name, class_name, start_time, course_name, level_name):
    msg = Message(
        subject="[Thông báo xác nhận đăng ký khóa học tại trung tâm ngoại ngữ ANQUINKO]",
        recipients=[to_email]
    )

    msg.html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 10px; overflow: hidden;">
            <div style="background-color: #ff8c00; padding: 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">XÁC NHẬN ĐĂNG KÝ</h1>
            </div>

            <div style="padding: 30px; background-color: #ffffff;">
                <p style="font-size: 18px;">Xin chào <strong>{name}</strong>,</p>
                <p>Chúc mừng bạn đã ghi danh thành công tại <strong>Trung tâm ngoại ngữ ANQUINKO</strong>. Dưới đây là thông tin chi tiết lớp học của bạn:</p>

                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #ff8c00;">
                    <p style="margin: 5px 0;"><strong>Khóa học:</strong> {course_name} ({level_name})</p>
                    <p style="margin: 5px 0;"><strong>Lớp học:</strong> {class_name}</p>
                    <p style="margin: 5px 0;"><strong>Ngày khai giảng dự kiến:</strong> <span style="color: #d9534f;">{start_time}</span></p>
                </div>

                <p>Chúng tôi sẽ gửi thông báo chi tiết nếu có bất kỳ thay đổi nào về lịch trình. Bạn vui lòng kiểm tra email thường xuyên nhé.</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000" style="background-color: #006400; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">TRUY CẬP TÀI KHOẢN</a>
                </div>

                <p style="font-size: 14px; color: #777;"><i>*Lưu ý: Nếu có thắc mắc, bạn chỉ cần phản hồi (Reply) trực tiếp email này.</i></p>
            </div>

            <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #888;">
                <p style="margin: 0;">&copy; 2025 Trung tâm ngoại ngữ ANQUINKO. All rights reserved.</p>
            </div>
        </div>
        """
    mail.send(msg)

if __name__ == '__main__':
    with app.app_context():
        send_register_success_email(
            "quinhquinhk5@gmail.com",
            "Test User",
            "IELTS 6.5"
        )
