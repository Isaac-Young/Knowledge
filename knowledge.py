import requests
from bs4 import BeautifulSoup
import re
import linecache
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#get the disambiguation word
def read_file(num, i):
    return linecache.getline("company.txt", num).strip().split('\t')[i]

#get url
def make_url(name):
    return "https://baike.baidu.com/item/" + name


def get_soup(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                      'Version/13.0.3 Safari/605.1.15'
    }
    html = requests.get(url, headers=headers, verify=False)
    if html.status_code == 200:
        html.encoding = 'utf-8' #utf-8
        return BeautifulSoup(html.text, 'html.parser')
    return None


def get_intro(obj):
    # title = obj.find('div', class_='lemma-summary')
    text = obj.find('div', attrs={'class': 'para'})
    if not text:####否则会报错'NoneType' object has no attribute 'get_text'
        return '无'
    result = text.get_text().split('\n')[0]
    return result


def get_attribute(soup):
    content = soup.find('div', class_='basic-info cmn-clearfix')
    if not content:####否则会报错'NoneType' object has no attribute 'get_text'
        return ''
    left = content.find('dl', attrs={'class': 'basicInfo-block basicInfo-left'}).get_text()
    right = content.find('dl', class_='basicInfo-block basicInfo-right').get_text()
    return left + right

#data clean and get list 
def split(s):
    list1 = s.strip().split('\n')
    list2 = []
    for i in list1:
        if i == '':
            continue
        if "\xa0" in i:
            i = "".join(i.split())
        if re.search('\[\d*\]', i):
            continue
        list2.append(i)
    return list2


def make_dict(str1, str2):
    return {'predicate': str1, 'object': str2}


def make(number, st, data, ring):
    return {"subject_id": number, "subject": st, "data": data, "fault": ring}



# user XJ
def unify_database(a,b,c,d):
    return{"entity_id": a, "entity_name": b, "kb_id": c, "entity_description": d}
# user XJ 
def unify_under(a,b,c,d):
    ls=[]
    ls.append(make_dict("摘要", a))
    ls.append(make_dict("类型", b))
    ls.append(make_dict("全名", c))
    ls.append(make_dict("股票号", d))
    return ls
#add one
def addOther(ent_id,ent_name,data,full_name):
    ls=unify_under(data,"其他",full_name,"NaN")  
    return unify_database(ent_id,ent_name,"-2",ls)

def addCompany(ent_id,ent_name,kb_id,data,full_name,StockNum):
    ls=unify_under(data,"公司",full_name,StockNum)
    return unify_database(ent_id,ent_name,kb_id,ls)





def make_data(s):
    url = make_url(s)
    soup = get_soup(url)
    intro = get_intro(soup)
    list1 = [make_dict('摘要', intro)]
    list2 = split(get_attribute(soup))
    # print(list2)
    i = 0
    while i < len(list2):
        a = make_dict(list2[i], list2[i + 1])
        list1.append(a)
        i += 2
    return list1


def get_href(soup):
    l = []
    t1 = soup.find_all('li', class_='item')
    for t2 in t1:
        t3 = t2.find('a')
        if None is not t3:
            t4 = "https://baike.baidu.com" + t3.get('href')
            l.append(t4)
    return l

#jump into the Baidu Encyclopedia's new Interpretation of the disambiguation word
def jump(s):
    url = make_url(s)
    soup = get_soup(url)
    l2 = get_href(soup)
    l1 = []
    for i in l2:
        soup = get_soup(i)
        text = get_intro(soup)
        obj = make_dict('摘要', text)
        l1.append(obj)
    return l1



def main():
    entity_id=-1;# knowledgebase id  
    alllist=[]
    for i in range(2, 329):#2,329
        kb_id = read_file(i, 0)
        stock_name = read_file(i, 1)
        stock_full_name = read_file(i, 2)#以全称搜索
        stock_code = read_file(i, 3)

        list1 = make_data(stock_full_name)
        datalist=[]
        for i in list1:
            if  i['predicate']=='摘要':
               datalist.append(i['object']) 
            else:
                datalist.append(i['predicate']+":"+i['object'])
        entity_id+=1
        result=addCompany(str(entity_id),stock_name,kb_id,''.join(datalist),stock_full_name,stock_code) #json.dumps(list1,ensure_ascii =False)
        alllist.append(result)
        print(result)
        
        list2 = jump(stock_name)#以简称搜索，但是有些其中存有全称的公司释义
        if len(list2):
            for i in list2:
                entity_id+=1
                result=addOther(str(entity_id),stock_name,i['object'],stock_name)
                alllist.append(result)
                print(result)
     
    
    with open('data.json','a+',encoding='utf-8') as f:    
        f.write(json.dumps(alllist,ensure_ascii =False))
    f.close()
if __name__ == '__main__':
    main()
