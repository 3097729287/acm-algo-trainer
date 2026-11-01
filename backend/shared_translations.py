"""Optional authenticated public statement cache; never receives draft/code/keys."""
import hashlib
import logging
from urllib.parse import urlencode

LOG=logging.getLogger('tb.shared-translations')


class SharedStatementTranslations:
    def __init__(self,training):self.training=training

    def owner(self):return self.training._ranking_profile().get('user_id')

    @staticmethod
    def identity(problem,original,format):
        return {'url':problem['url'],'sourceHash':hashlib.sha256((format+'\n'+original).encode()).hexdigest(),'format':format,'language':'zh-CN'}

    def get(self,problem,original,format):
        profile=self.training._ranking_profile()
        if not profile.get('endpoint') or not profile.get('auth_token'):return None
        try:
            value=self.training.leaderboard._request(profile,'GET','/v1/translations?'+urlencode(self.identity(problem,original,format)),timeout=2)
            translation=value.get('translation')
            from insights import canonical_url
            if not isinstance(translation,dict) or translation.get('sourceHash')!=self.identity(problem,original,format)['sourceHash'] or translation.get('language')!='zh-CN' or translation.get('format')!=format or canonical_url(translation.get('url'))!=canonical_url(problem['url']):return None
            from translation import validate_translation
            validate_translation(original,translation.get('markdown') or '')
            return translation['markdown']
        except (RuntimeError,ValueError,TypeError):return None
        except Exception as error:
            if getattr(error,'status',None) is not None:return None
            raise

    def publish(self,problem,original,markdown,format,expected_owner=None):
        profile=self.training._ranking_profile()
        if not profile.get('endpoint') or not profile.get('auth_token') or expected_owner is not None and profile.get('user_id')!=expected_owner:return False
        # Only these public statement fields cross this boundary. Provider
        # configuration, account names and editor content are never serialized.
        body={**self.identity(problem,original,format),'original':original,'markdown':markdown}
        try:return self.training.leaderboard._request(profile,'POST','/v1/translations',body,timeout=3).get('saved') is True
        except Exception as error:LOG.debug('Shared statement upload deferred: %s',type(error).__name__)
        return False
