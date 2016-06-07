# coding:utf-8
import re
import copy
import sys
import urllib2
import urllib
import cookielib
import json
import time
import datetime
from StringIO import StringIO
import gzip
from bs4 import BeautifulSoup


current_time = time.strftime("%Y%m%d%H%M%S")
login_data = {
    'username': 'caozijun007@163.com',
    'password': 'aaa123',
    'rememberMe': 'false',
}
pc_create_data = {
    'name': 'name test',
    'type': '101',
    'pageMode': '2',
    'description': 'description test'
}
app_create_data = {
  "scene": {
    "pageMode": "1",
    "name": "APP test example",
    "type": "1",
    "description": "This is my APP test example"
  },
  "pages": [
    {
    }
  ]
}

home_url = 'http://eqxiu.com/home'
login_url = 'http://service.eqxiu.com/login'
create_url = 'http://service.eqxiu.com/m/scene/create'
app_create_url = 'http://m1.eqxiu.com/m/app/scene/merge/create'
detail_basic_url = 'http://service.eqxiu.com/m/scene/detail'
pageList_basic_url = 'http://service.eqxiu.com/m/scene/pageList'
saveSettings_url = 'http://service.eqxiu.com/m/scene/saveSettings'
save_url = 'http://service.eqxiu.com/m/scene/save'
app_save_url = 'http://m1.eqxiu.com/m/scene/page/batchSave'
createPage_basic_url = 'http://service.eqxiu.com/m/scene/createPage'
delPage_url = 'http://service.eqxiu.com/m/scene/delPage'
publish_basic_url = 'http://service.eqxiu.com/m/scene/publish'

def opener():
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'),
        ('Connection', 'Keep-alive'),
        ('Accept', 'application/json, text/plain'),
        ('Accept-Encoding', 'gzip, deflate'),
        ('Accept-Language', 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4'),
        ('Host', 'service.eqxiu.com'),
        ('Origin', 'http://eqxiu.com'),
        ('Referer', 'http://eqxiu.com/home/login'),
        ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')]
    return opener


def gzip_reader(data):
    buf = StringIO(data.read())
    f = gzip.GzipFile(fileobj=buf)
    jsoned_data = json.loads(f.read())
    return jsoned_data


def json_reader(data):
    return json.loads(data)


def timestamp():
    return str(int(time.time()*1000))


def post_data_to_url(url, data):
    data_encoded = urllib.urlencode(data)
    req = urllib2.Request(url, data_encoded)
    try:
        resp = urllib2.urlopen(req)
        data = gzip_reader(resp)
        return data
    except urllib2.URLError, ex:
        print 'Error code:', ex.reason


def post_json_to_url(url, data):
    if isinstance(data, dict):
        data = json.dumps(data)

    req = urllib2.Request(url, data)
    try:
        resp = urllib2.urlopen(req)
    except urllib2.URLError, ex:
        print 'Error code:', ex.reason
    return resp


def post_json_to_url_get_gzip(url, data):
    if isinstance(data, dict):
        data = json.dumps(data)

    req = urllib2.Request(url, data)
    try:
        resp = urllib2.urlopen(req)
        data = gzip_reader(resp)
    except urllib2.URLError, ex:
        print 'Error code:', ex.reason
    return data


def get_data_from_url(url):
    resp = urllib2.urlopen(url)
    resp_text = gzip_reader(resp)
    if 200 != resp_text['code']:
        print "Code:" + resp_text['code'] + ", msg:" + resp_text['msg']
        sys.exit(0)
    else:
        return resp_text

def copy_eqxiu_to_eqxiu(show, login_info):

    login_result = post_data_to_url(login_url, login_info)
    if login_result['code'] != 200:
        print login_result['msg']
        sys.exit(0)
    if int(show.get_setting('type')) <= 100:
        data = post_json_to_url_get_gzip(app_create_url, app_create_data) # create a new scene distinguished by type
        sceneId = data['obj']['id']
    else:
        data = post_data_to_url(create_url, pc_create_data)  # get the scene id
        sceneId = data['obj']

    scene_id = []
    pageList_url = pageList_basic_url + '/' + str(sceneId) + '?date=' + timestamp()
    resp_text = get_data_from_url(pageList_url)
    scene_id.append(resp_text['list'][0]['id'])  # get the default page id

    for i in range(0, show.pages):
        if i in show.longPage.keys():
            createPage_url = createPage_basic_url + '/' + str(scene_id[-1]) + '?longPage=' + str(show.longPage[i]) + '&time=' + timestamp()
        else:
            createPage_url = createPage_basic_url + '/' + str(scene_id[-1]) + '?time=' + timestamp()

        response_text = get_data_from_url(createPage_url)  # add new page in the scene

        pageList_url = pageList_basic_url + '/' + str(sceneId) + '?date=' + timestamp()
        resp_text = get_data_from_url(pageList_url)  # get id of the new page
        try:
            scene_id.append(resp_text['list'][i+1]['id'])
        except IndexError:
            print "The scene_id is:"
            print scene_id
    else:
        delete_page_url = delPage_url + '/' + str(scene_id[0])
        get_data_from_url(delete_page_url)
        del scene_id[0]

    detail_url = detail_basic_url + '/' + str(sceneId)
    resp_text = get_data_from_url(detail_url)['obj']

    resp_text['name'] = show.get_setting('name') + current_time  # change the scene name
    resp_text['updateTime'] = timestamp()
    resp_text['description'] = show.get_setting('description')
    resp_text['pageMode'] = show.get_setting('pageMode')
    resp_text['cover'] = show.get_setting('cover')
    resp_text['bgAudio'] = show.get_setting('bgAudio')
    resp_text['property'] = show.get_setting('property')
    resp_text['bizType'] = show.get_setting('bizType')
    resp_text['type'] = show.get_setting('type')
    result = post_json_to_url_get_gzip(saveSettings_url, resp_text)  # update the setting
    if result['code'] != 200:
        print 'set the setting failed,reason:' + str(result['msg'].encode('utf-8'))
        # print resp_text['property']
        # print resp_text['property'] .rsplit('triggerLoop', 1)[0]
        # # temp = resp_text['property'].split('EqAd":', 1)[0] + 'false' + resp_text['property'] .rsplit(',"last', 1)[1]
        # # print temp
    for i in range(show.pages):
        spider_data = copy.deepcopy(show.objects['list'][i])
        spider_data['id'] = scene_id[i]  # set the page id
        spider_data['sceneId'] = sceneId  # set the scene id
        # set the page link
        for k in spider_data['elements']:
            k['pageId'] = scene_id[i]
            k['sceneId'] = sceneId
            if 'url' in k['properties']:
                for j in range(show.pages):
                    id_in_loop = show.objects['list'][j]['id']
                    if id_in_loop == k['properties']['url']:
                        k['properties']['url'] = scene_id[j]
                        break
        if int(show.get_setting('type')) < 100:
            post_json_to_url(app_save_url, spider_data)  # save the scene by page distinguished by type
        else:
            post_json_to_url(save_url, spider_data)
    publish_url = publish_basic_url + '?id=' + str(sceneId) + '&time=' + timestamp()
    get_data_from_url(publish_url)
    print 'Successfully save the scene:' + show.get_setting('name') + current_time


class Scene:
    def __init__(self, url):
        self.url = url
        self.content = self.get_scene
        self.id = self.get_setting('id')
        self.objects = self.get_scene_object()
        self.shareCount = self.objects['map']['shareCount']
        self.pages = len(self.objects['list'])
        self.longPage = self.get_long_pages()

    @property
    def get_scene(self):

        """
        Return the scene setting content from the source url
        """
        url_content = urllib2.urlopen(self.url).read()
        soup = BeautifulSoup(url_content.decode('utf-8'), 'html.parser')

        soup_target = soup.find_all('script')[-1]
        match_case = r"scene = {(.*)};"
        m = re.search(match_case, soup_target.string.replace('\n', ''))
        return m.group(1)

    def get_scene_object(self):

        """
        return the object which is used by the target scene of id
        """

        timestamp = int(time.time()*1000)
        base_url = 'http://s6.eqxiu.com/eqs/page/'
        final_url = base_url + str(self.id) + '?time=' + str(timestamp)

        url_content = urllib2.urlopen(final_url).read().decode('utf-8')
        decoded_json = json.loads(url_content)

        return decoded_json

    def get_long_pages(self):
        long_page = {}
        for index, item in enumerate(self.objects['list']):
            if item['properties'] and 'longPage' in item['properties']:
                long_page[index] = item['properties']['longPage']
        return long_page

    def get_setting(self, key):
        if key == 'property':
            match_case = key + r':\'(.+?)\''
        elif key == 'bgAudio':
            match_case = key + r':(.+?),property'
        else:
            match_case = key + r':(.+?),'
        result = re.search(match_case, self.content)
        if key == 'bgAudio' and result.group(1) == 'null':
            return None
        if key == 'property':
            property_result = result.group(1).strip().strip("\"").strip("\'")
            property_slices = property_result.split('true', 1)
            if property_slices[0].endswith('hideEqAd\":'):
                property_result = ''.join(property_slices[0] + 'false' + property_slices[1])
                return property_result
        return result.group(1).strip().strip("\"").strip("\'")

def main_copyer(url, username, psw):
    t0 = time.clock()

    login_data['username'] = username
    login_data['password'] = psw

    show_scene = Scene(url)
    urllib2.install_opener(opener())
    copy_eqxiu_to_eqxiu(show_scene, login_data)

    print 'It takes ' + str('%0.5f' % (time.clock()-t0)) + ' seconds'

if __name__ == '__main__':
    # scene_url = raw_input("Enter the scene url:")
    # user_name = raw_input("Enter your user name:")
    # user_psw = raw_input("Enter your user password:")
    # if not scene_url:
    #     scene_url = 'http://e.eqxiu.com/s/ROTTjWxu'
    # if user_name:
    #     login_data['username'] = user_name
    # if user_psw:
    #     login_data['password'] = user_psw
    if len(sys.argv) <= 1:
        scene_url = 'http://e.eqxiu.com/s/ROTTjWxu'
    elif len(sys.argv) <= 2:
        scene_url = sys.argv[1]
    else:
        scene_url = sys.argv[1]
        login_data['username'] = sys.argv[2]
        login_data['password'] = sys.argv[3]

    t0 = time.clock()


    # show_scene = Scene('http://eqxiu.com/s/rkQAcctR')  # test copy page
    # show_scene = Scene('http://eqxiu.com/s/DJkHVis6')  # test copy page
    # show_scene = Scene('http://e.eqxiu.com/s/ROTTjWxu')  # mix test
    # show_scene = Scene('http://eqxiu.com/s/vGWzfJA4')  # model test
    # show_scene = Scene('http://eqxiu.com/s/bCS7ikea')  # single long page test
    # show_scene = Scene('http://h.eqxiu.com/s/zJd5yB1f?from=groupmessage&isappinstalled=0')
    # show_scene = Scene('http://eqxiu.com/s/7MNjdgKr')
    # show_scene = Scene('http://eqxiu.com/s/5m5hnGyB')
    # show_scene = Scene('http://e.eqxiu.com/s/rz1QJRg9')  # cancel the last page (Pay)
    # show_scene = Scene('http://h5.eqxiu.com/s/QXXu1QhA')  # all images scene

    show_scene = Scene(scene_url)
    urllib2.install_opener(opener())
    copy_eqxiu_to_eqxiu(show_scene, login_data)

    print 'It takes ' + str('%0.5f' % (time.clock()-t0)) + ' seconds'
