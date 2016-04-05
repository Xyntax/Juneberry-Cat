# /bin/python
# -*- coding:utf-8 -*-
import time
import sys
import requests
from bs4 import BeautifulSoup
from mail import sendmail

__author__ = 'xy'


class FUCK():
    def __init__(self, username, password, seatNO, mailto):

        self.username = username
        self.password = password
        self.seatNO = seatNO
        self.mailto = mailto
        self.base_url = 'http://yuyue.juneberry.cn'
        self.login_url = 'http://yuyue.juneberry.cn'
        self.order_url = self._get_order_url()

        self.login_content = ''
        self.middle_content = ''
        self.final_content = ''

        self.s = requests.session()  # 创建可传递cookies的会话

        # post data for login
        self.data1 = {
            'subCmd': 'Login',
            'txt_LoginID': self.username,  # S+学号
            'txt_Password': self.password,  # 密码
            'selSchool': 60,  # 60表示北京交通大学
        }

        # post data for order a seat
        self.data2 = {
            'subCmd': 'query',
        }

        # 自定义http头，然而我在程序里并没有使用
        self.headers = {
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        self.login()
        self.run()
        self._is_success(self.final_content)

        # 怀疑程序出错时，取消下行注释，可打印一些参数
        # self._debug()

    def _get_date_str(self):
        s = time.localtime(time.time())
        ########333
        date_str = str(s.tm_year) + '%2f' + str(s.tm_mon) + '%2f' + str(s.tm_mday + 1)
        date_str = date_str.replace('%2f1%2f32', '%2f2%2f1') \
            .replace('%2f2%2f29', '%2f3%2f1') \
            .replace('%2f3%2f32', '%2f4%2f1') \
            .replace('%2f4%2f31', '%2f5%2f1') \
            .replace('%2f5%2f32', '%2f6%2f1') \
            .replace('%2f6%2f31', '%2f7%2f1') \
            .replace('%2f7%2f32', '%2f8%2f1') \
            .replace('%2f8%2f32', '%2f9%2f1') \
            .replace('%2f9%2f31', '%2f10%2f1') \
            .replace('%2f10%2f32', '%2f11%2f1') \
            .replace('%2f11%2f31', '%2f12%2f1') \
            .replace('%2f12%2f32', '%2f1%2f1')
        return date_str

    def _get_order_url(self):
        return "http://yuyue.juneberry.cn/BookSeat/BookSeatMessage.aspx?seatNo=101001" + self.seatNO + "&seatShortNo=01" + self.seatNO + "&roomNo=101001&date=" + self._get_date_str()

    def _get_static_post_attr(self, page_content, data_dict):
        """
        拿到<input type='hidden'>的post参数，并添加到post_data中
        """
        soup = BeautifulSoup(page_content, "html.parser")
        for each in soup.find_all('input'):
            if 'value' in each.attrs and 'name' in each.attrs:
                data_dict[each['name']] = each['value']  # 添加到login的post_data中
                # self.data2[each['name']] = each['value']  # 添加到order的post_data中
        return data_dict

    def _debug(self):

        print self.order_url
        print self.data1
        print self.data2
        print self.headers
        print self.s.cookies

        # print self.login_content
        # print self.middle_content
        print self.final_content

    def login(self):
        homepage_content = self.s.get(self.base_url).content
        self.data1 = self._get_static_post_attr(homepage_content, self.data1)
        r = self.s.post(self.login_url, self.data1)
        self.login_content = r.content

    def run(self):

        # 这个get的意思是：原先的cookie没有预约权限，
        # 访问这个get之后，会使cookie拥有预约权限，从而执行下一个post
        self.middle_content = self.s.get('http://yuyue.juneberry.cn/BookSeat/BookSeatListForm.aspx').content

        # 经测试，这个post只需要一个subCmd的参数就可以正常返回，因此不必根据get内容更新post参数
        # self.data2 = self._get_static_post_attr(middle_content, self.data2)

        # 这个post请求完成了预约功能！
        r = self.s.post(self.order_url, self.data2)

        self.final_content = r.content

    def _is_success(self, text):
        """
        接受最终的html内容，判断是否成功，并触发日志记录和邮件提醒
        """
        if '<h5 id="MessageTip">已经存在有效的预约记录。</h5>' in text:
            self.clear_error_once('[done!] You already ordered a seat!')
        elif '<h5 id="MessageTip">选择的日期不允许预约。</h5>' in text:
            self.clear_error_once('[done!] Date is wrong!')
        elif '<h5 id="MessageTip">所选座位已经被预约。</h5>' in text:
            self.clear_error_once('[done!] This seat is not available, maybe taken by others!')
        elif '<h5 id="MessageTip">座位预约成功' in text:
            self.clear_error_once('[done!] Success! An email is sending to you!')
            sendmail.send_mail('BJTU Library Seat_NO:' + self.seatNO + 'ordered!',
                               'Sending by robot. Do not reply this mail!', self.mailto)
        else:
            self.error_log_once('Error! 302 to login page')

    def error_log_once(self, text='default error (once)'):
        try:
            is_error_file = open('./isopen_xy.txt', 'r')
        except:
            is_error_file = open('./isopen_xy.txt', 'w')
        if '1' not in is_error_file.read():
            print 'writting error to log...'
            self.error_log(text)
        else:
            print 'already written to log'
        is_error_file.close()
        sendmail.send_mail('BJTU_Library system error once !', 'error text!')

    def error_log(self, text='default error'):
        is_error_file = open('./isopen_xy.txt', 'w')
        is_error_file.write('1\n')
        is_error_file.close()

        f = open("./log_xy.txt", 'a')
        f.write(time.strftime("%Y-%m-%d %X", time.localtime()) + text + '\n')
        f.close()

    def clear_error_once(self, text='success'):
        print text
        is_error_file = open('./isopen_xy.txt', 'w')
        is_error_file.write('0\n')
        is_error_file.close()


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print 'Usage: python library.py [username] [password] [seat_NO] [email]'
        print 'eg. python library.py S13280001 123456 003 XXXX@qq.com\n'
        print 'Any problems, mail to: i[at]cdxy.me'
        print '#-*- Edit by cdxy 16.03.24 -*-'
        sys.exit(0)
    else:
        FUCK(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
