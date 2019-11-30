# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 16:16:16 2019

@author: John
"""

import imaplib, re
#from headerparser import HeaderParser
import email
import http.cookiejar
import urllib.parse
import urllib.request
import requests
import logging
import os

#from boxx import p,g

class pygmail(object):
    def __init__(self):
        self.IMAP_SERVER='imap.163.com'
        self.IMAP_PORT=993
        self.M = None
        self.response = None
        self.mailboxes = []
        
        # set tmp dir
        self.tmp_dir='tmp_dir'
        isExists=os.path.exists(self.tmp_dir)
        if not isExists:
                os.makedirs(self.tmp_dir) 
        
        #set log
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(self.tmp_dir+"\\log.txt",encoding='utf-8')
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.addHandler(console)
 
    def login(self, username, password):
        self.M = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
        rc, self.response = self.M.login(username, password)
        return rc
    
    def parse_paper_in_mail(self, message):
        """ get paper title in google scholar alert """
        ret = 1
        body_list=[]
        pattern=re.compile(r'(?<=#1a0dab\">).*?(?=</a>)')
        for msg in message:
            paper_list=[]
            for part in msg.walk():
                if not part.is_multipart():
                        body=part.get_payload(decode=True)
                        body_str=body.decode('utf-8')
                        paper_list=re.findall(pattern,body_str)
                        for paper_idx,paper in enumerate(paper_list):
                            # replace invalid characters
                            paper=re.sub(u"\\<.*?\\>", "", paper)
                            paper=paper.replace('&#39;','\'')
                            paper=paper.replace('” ','')
                            paper=paper.strip('.\\"')
                            paper=paper.replace(':','_')
                            paper_list[paper_idx]=paper
                        body_list.append(paper_list)
        return ret,body_list
   
    
    def get_unread_mail(self, folder='INBOX'):
        """ get unseen mail in inbox folder """
        status, count = self.M.select(folder, readonly=1)
        
        # get unseen mail id
        rc, self.response = self.M.search(None, '(UNSEEN)')
        unseen_mail_num=len(self.response[0].split())
        if(unseen_mail_num==0):
            self.logger.warning('\n\nNo unseen mail')
            ret = 0
        else:
            self.logger.warning('\n\nGet %d unseen mail'%unseen_mail_num)
            ret = 1
        
        # fetch mail body
        unseen_mail_data = []
        for mail in self.response[0].split():  
            rc, datas = self.M.fetch(mail, '(RFC822)')
            mail_data = email.message_from_bytes(datas[0][1])
            unseen_mail_data.append(mail_data)
        return ret,unseen_mail_data
 
    
    def download_from_googlescholar(self,paper):

#        url = "https://kuaisou.99lb.net/php/xs.php?hl=zh-CN&as_sdt=0%2C5&q=+" + paper_tmp + "&btnG="
        url = "https://f.glgoo.top/scholar?ie=utf-8&shb=1&src=%E5%BF%AB%E6%90%9Csou_newhome&q=+" + paper.replace(' ','+') 
        header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        req = urllib.request.Request(url=url, headers=header_dict)
        try :
            response = opener.open(req)
        except UnicodeEncodeError :
            return 0

        data = response.read()
        data = data.decode()
        pattern = re.compile(r'href="(http.+?.pdf)"')
        result1 = re.findall(pattern, data)
        pattern2 = re.compile(r'href="(http.+?/pdf.+?)"')
        result2 = re.findall(pattern2, data)
        if result1:
            result = result1[0]
        elif result2:
            result = result2[0]
        else:
            return 0
        
        try:
            imgres = requests.get(result)
        except ConnectionError :
            return 0
        
        try:
            with open(self.tmp_dir+"\\{}.pdf".format(paper), "wb") as f:
                if not f:
                    return 0
                f.write(imgres.content)
                return 1
        except FileNotFoundError :
            return 0
        
    def download_all_papers(self,papers_list):
        for list_idx,paper_list in enumerate(papers_list):
            for idx,paper in enumerate(paper_list):
                ret = self.download_from_googlescholar(paper)
                if ret==1:
                    self.logger.info('[Success] download %d/%d in mail %d/%d [title]:%s'%(idx+1,len(paper_list),list_idx+1,len(papers_list),paper))
                else:
                    self.logger.warning('[Fail] download %d/%d in mail %d/%d [title]:%s'%(idx+1,len(paper_list),list_idx+1,len(papers_list),paper))     
        return 1
    def logout(self):
        self.M.logout()
 
if __name__ =="__main__":
    demo=pygmail()
    demo.login("*******@163.com","******")#(username,password)

    ret,mail=demo.get_unread_mail()
    assert ret==1
    
    ret,papers=demo.parse_paper_in_mail(mail)
    assert ret==1
        
    ret = demo.download_all_papers(papers)
    assert ret==1
    demo.logout()
    print('All works are done, please download failed papers manually!')