# -*- coding: utf8 -*-
__author__ = 'xy'

import smtplib
from email.mime.text import MIMEText


def send_mail(title='default_title', content='default_content',
              to_list_='941335582@qq.com'):
    to_list = []
    to_list.append(to_list_)
    mail_host = "smtp.163.com"    #smtp server
    mail_user = "XXXXX@163.com"  #your mail address
    mail_pass = "XXXXXX"          #your pass
    # mail_postfix = "163.com" 

    me = "XXXXX@163.com"   # mail from
    msg = MIMEText(content, _subtype='html', _charset='gb2312')
    msg['Subject'] = title
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        s = smtplib.SMTP()
        s.connect(mail_host)
        s.login(mail_user, mail_pass)
        s.sendmail(me, to_list, msg.as_string())
        s.close()
        return True
    except Exception, e:
        print str(e)  # print error log
        return False

