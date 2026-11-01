"""Recognize original-site access notices without treating them as statements."""
import re

class StatementAccessRequired(ValueError):
    pass

def nowcoder_access_notice(page):
    return bool(re.search(r'<title\b[^>]*>[^<]*(?:报名后才能查看题目|登录后才能查看|请先登录)',page,re.I)
                or re.search(r'class=["\'][^"\']*\bnull-tip\b[^"\']*["\'][^>]*>\s*(?:报名后才能查看题目|登录后才能查看)',page,re.I))
