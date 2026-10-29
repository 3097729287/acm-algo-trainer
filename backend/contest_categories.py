"""Contest series and actual hosting platform are independent filters."""
import re

def is_acm(row):
    name=str(row.get('contest') or row.get('name') or '')
    return row.get('series')=='XCPC' or bool(re.search(r'ICPC|CCPC|XCPC|ACM|区域赛|邀请赛|省赛|网络(?:预选)?赛|分区赛|大学生.*程序设计',name,re.I))

def matches_shelf(row,shelf):
    if not shelf or shelf=='all':return True
    if shelf.casefold() in ('xcpc','acm'):return is_acm(row)
    lanqiao=str(row.get('series') or row.get('contest') or '').startswith('蓝桥杯')
    if shelf=='lanqiao':return lanqiao
    return shelf.casefold()==str(row.get('platform','')).casefold()
