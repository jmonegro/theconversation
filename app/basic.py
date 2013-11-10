import tornado.web

import settings
import simplejson as json

from lib import userdb

class BaseHandler(tornado.web.RequestHandler):
  def render(self, template, **kwargs):
    kwargs['is_admin'] = 'false'
    kwargs['tinymce_valid_elements'] = ''
    kwargs['post_char_limit'] = 1000
    kwargs['user_id_str'] = ''
    kwargs['user_email_address'] = ''
    kwargs['is_staff'] = False
    kwargs['see_admin_link'] = False
    kwargs['sticky'] = False
    kwargs['is_blacklisted'] = False

    super(BaseHandler, self).render(template, **kwargs)

  def get_current_user(self):
    return self.get_secure_cookie("username")

  def send_email(self, from_user, to_user, subject, text):
    sendgrid = self.settings['sendgrid']
    return sendgrid.send_email(lambda x: None, **{
      'from': from_user,
      'to': to_user,
      'subject': subject,
      'text': text,
    })

  def is_blacklisted(self, screen_name):
    u = userdb.get_user_by_screen_name(screen_name)
    if u and 'user' in u.keys() and 'is_blacklisted' in u['user'].keys() and u['user']['is_blacklisted']:
      return True
    return False

  def current_user_can(self, capability):
    """
    Tests whether a user can do a certain thing.
    """
    result = False
    u = userdb.get_user_by_screen_name(self.current_user)
    if u and 'role' in u.keys():
      try:
        if capability in settings.get('%s_capabilities' % u['role']):
          result = True
      except:
        result = False
    return result

  def api_response(self, data):
    # return an api response in the proper output format with status_code == 200
    self.write_api_response(data, 200, "OK")

  def error(self, status_code, status_txt, data=None):
    # return an api error in the proper output format
    self.write_api_response(status_code=status_code, status_txt=status_txt, data=data)

  def write_api_response(self, data, status_code, status_txt):
    # return an api error based on the appropriate request format (ie: json)
    format = self.get_argument('format', 'json')
    callback = self.get_argument('callback', None)
    if format not in ["json"]:
      status_code = 500
      status_txt = "INVALID_ARG_FORMAT"
      data = None
      format = "json"
    response = {'status_code':status_code, 'status_txt':status_txt, 'data':data}

    if format == "json":
      data = json.dumps(response)
      if callback:
        self.set_header("Content-Type", "application/javascript; charset=utf-8")
        self.write('%s(%s)' % (callback, data))
      else:
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(data)
      self.finish()
