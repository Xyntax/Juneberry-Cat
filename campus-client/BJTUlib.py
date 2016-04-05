# /bin/python
# -*- coding:utf-8 -*-
import time
import sys
import requests
from bs4 import BeautifulSoup
from mail import sendmail
import re

__author__ = 'xy'


class FUCK():
    def __init__(self, username, password, seatNO, mailto):

        self.username = username
        self.password = password
        self.seatNO = seatNO
        self.mailto = mailto
        self.date_str = self._get_date_str()
        self.base_url = 'http://202.112.150.5:82/'
        self.login_url = self.base_url + '/default.aspx'

        self.login_content = ''
        self.middle_content = ''
        self.final_content = ''

        self.mail_message = "Seat:" + seatNO + \
                            "<br>Start at" + time.strftime("%Y-%m-%d %X", time.localtime()) + '<br>'
        self.s = requests.session()  # 创建可传递cookies的会话


        # 自定义http头，终端校检了referer
        self.headers = {
            'Accept': 'text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://202.112.150.5:82/',
            'Connection': 'keep-alive',
        }

        self.login()
        self.run()

    def _get_date_str(self):
        s = time.localtime(time.time())
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

    def _get_static_post_attr(self, page_content):
        """
        拿到<input type='hidden'>的post参数，并return
        """
        _dict = {}
        soup = BeautifulSoup(page_content, "html.parser")
        for each in soup.find_all('input'):
            if 'value' in each.attrs and 'name' in each.attrs:
                _dict[each['name']] = each['value']
        return _dict

    def _get_static_get_attr(self, page_content):
        """
        <div id='101001215'
        class='CanBespeakSeat'
        style='left: 630px; top: 840px;width: 42px;height: 42px;'

        onclick='BespeakSeatClick("2F29783C655A9563339AB02D15E6D524932B751B7D8BD46802F5BDE0A018D003503E2518F9C5AB5225C8425EFC3702B5D3068D5DFD018711A0A9E535A46B81CE27D88419D3F89E0CCDC4033307521FB0")'
        onmouseover='tipShow(this,"可预约")'
        """

        _str = re.compile("<div id='101001" + self.seatNO + "'(.*?)</div>")
        ans_str = re.findall(_str, page_content)
        # print ans_str

        _str1 = re.compile("BespeakSeatClick\(\"(.*?)\"\)")
        seat_str = re.findall(_str1, ans_str[0])
        # print seat_str

        if seat_str[0] == "":
            self.mail_message += "This seat is taken by others!<br>System exit!<br>"
            sendmail.send_mail('error text!', self.mail_message, self.mailto)
            print "This seat is taken by others!\nSystem exit!"
            sys.exit(0)
        else:
            self.mail_message += seat_str[0]
            self.mail_message += '<br>'
            return seat_str[0]

    def login(self):
        homepage_content = self.s.get(self.base_url).content
        data = self._get_static_post_attr(homepage_content)

        data['txtUserName'] = self.username
        data['txtPassword'] = self.password
        data['cmdOK.x'] = 1
        data['cmdOK.y'] = 1

        r = self.s.post(self.login_url, data)
        self.login_content = r.content
        # print r.content

    def run(self):

        data_middle = {
            'roomNum': '101001 ',
            'date': self._get_date_str().replace('%2f', '/') + ' 0:00:00',
            'divTransparentTop': '0',
            'divTransparentLeft': '0'
        }

        middle_url = self.base_url + "/FunctionPages/SeatBespeak/SeatLayoutHandle.ashx"

        self.middle_content = self.s.post(
            middle_url,
            data=data_middle,
            headers=self.headers
        ).content
        # print self.middle_content

        get_para = self._get_static_get_attr(self.middle_content)

        self.final_url = self.base_url + "/FunctionPages/SeatBespeak/BespeakSubmitWindow.aspx?parameters=" + get_para

        # 这里校检了referer
        _headers = {
            'Referer': self.base_url + 'FunctionPages/SeatBespeak/BespeakSeatLayout.aspx'
        }

        final_dict = self._get_static_post_attr(self.s.get(self.final_url, headers=_headers).content)
        print final_dict
        final_dict["__EVENTTARGET"] = "ContentPanel1$btnBespeak"
        final_dict["__EVENTARGUMENT"] = ""
        final_dict["X_CHANGED"] = "false"
        final_dict["X_TARGET"] = "ContentPanel1_btnBespeak"
        final_dict["Form2_Collapsed"] = "false"
        final_dict["ContentPanel1_Collapsed"] = "false"
        final_dict["X_STATE"] = ""
        final_dict["X_AJAX"] = "true"

        self.final_content = self.s.post(
            self.final_url, data=final_dict, headers=self.headers
        ).content

        print self.final_content

        is_success = False
        if "X.wnd.getActiveWindow()" in self.final_content:
            is_success = True

        if is_success:
            sendmail.send_mail('Get Seat_NO: ' + self.seatNO + ' success!',
                               self.mail_message, self.mailto)
        else:
            sendmail.send_mail('Error Log', self.mail_message, self.mailto)


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print 'Usage: python BJTUlib.py [username] [password] [seat_NO] [email]'
        print 'eg. python BJTUlib.py S13280001 123456 003 XXXX@qq.com\n'
        print 'Any problems, mail to: i[at]cdxy.me'
        print '#-*- Edit by cdxy 16.03.24 -*-'
        sys.exit(0)
    else:
        FUCK(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
