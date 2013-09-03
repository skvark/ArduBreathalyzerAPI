"""
Simple CherryPy API for Arduino breathalyzer.

This is the main API.
- dbwrapper wraps the heroku postgresql database stuff
- servicewrapper wraps some social media API's

For more information about usage see documentation.

"""
import json
import cherrypy
import urllib
import os

import dbwrapper
import servicewrapper


class API(object):

    exposed = True

    def __init__(self):
        pass

    def GET(self, authtoken, user, year, week=None, day=None):
        """ Gets user data. Year must be given, week and day are optional. """

        cherrypy.response.headers['Content-Type'] = 'application/json'

        data = dbwrapper.get_user_data(user, authtoken, year, week, day)
        return json.dumps(data)

    GET.exposed = True

    def POST(self, user, authtoken, bac, service=None, latitude=None, longtitude=None):
        """ Adds new BAC entry for user. Returns a dict containing
            database insert and service post statuses. """

        cherrypy.response.headers['Content-Type'] = 'application/json'

        status = {'db': 'false', 'social': 'false'}

        if dbwrapper.check_authtoken(authtoken):

            # convert strings to float
            try:
                bac = float(bac)
            except:
                # bac can't be empty so failure is imminent
                return json.dumps(status)

            try:
                lat = float(latitude)
                lon = float(longtitude)
            except:
                lat = None
                lon = None

            # post data, further validity checks done in wrappers
            data = dbwrapper.get_user_data(authtoken)
            db = dbwrapper.insert_bac_data(data[0], bac, lat, lon, service)

            if service != None:
                social = servicewrapper.post(authtoken, bac, service, lat, lon)
                status['social'] = social

            status['db'] = db

        return json.dumps(status)

    POST.exposed = True


class ArduBreathalyzer(object):

    exposed = True

    def __init__(self):

        self._services = {'Twitter': '', 'Facebook': '', 'Foursquare': ''}
        self._statuses = {'twt': False, 'fq': False, 'fb': False}
        self._callback_url = os.environ['URL'] + '/success'
        self._show_services = True

    def index(self):

        services = dbwrapper.get_available_services()

        if len(services) != 0:
            self._show_services = False

        if self._show_services:

            return '\
            <form action="add_services" method="post">\
            <p>Twitter Consumer Key:</p>\
            <input type="text" name="twt_key"/>\
            <p>Twitter Consumer Secret:</p>\
            <input type="text" name="twt_secret" />\
            <p>Foursquare Client id:</p>\
            <input type="text" name="fq_key"/>\
            <p>Foursquare Client secret:</p>\
            <input type="text" name="fq_secret" />\
            <p>Facebook app id:</p>\
            <input type="text" name="fb_app_id"/>\
            <p>Facebook app secret:</p>\
            <input type="text" name="fb_app_secret"/>\
            <p><input type="submit" value="Link applications"/></p>\
            </form>'

        else:

            return '<html>API index.<br /><a href="add_user">Add new user</a></html>'

    index.exposed = True

    def add_user(self, **kwargs):
        """ Adds new user to database. Returns the authtoken for that user.
            Only services which are supported are shown.
        """

        form = []
        services = dbwrapper.get_available_services()

        for service in services:

            form.append('\
            <input type="hidden" name="{0}" value="" />\
            <input type="checkbox" name="{0}" value="{0}" />\
            {0}'.format(service))

        data = ''.join(form)

        return '<p>You will be redirected to the selected services\
                one by one for authorization purposes.</p>\
                <p>After that you will get unique authorization token to use\
                with Arduino or other software. <p><b>It will be shown only once\
                so save it somewhere safe and keep it to yourself!</b></p>\
                <p>It is highly discouraged to use this API with your own social media accounts.</p>\
                <form action="oauth_dance" method="post">\
                <p>Username:</p>\
                <input type="text" name="user"/>\
                <p>Select services to use with your account:</p>\
                %s\
                <p><input type="submit" value="Create user"/></p>\
                </form>' % data

    add_user.exposed = True

    def add_services(self, **kwargs):
        """ Checks tokens and adds services to the database. """

        if self._show_services:

            successfull = []
            unsuccessfull = []

            if servicewrapper.check_consumer_tokens('Twitter',
                                                     kwargs['twt_key'],
                                                     kwargs['twt_secret']):

                dbwrapper.insert_service_data('Twitter',
                                               kwargs['twt_key'],
                                               kwargs['twt_secret'])
                successfull.append('Twitter')
            else:
                unsuccessfull.append('Twitter')

            if servicewrapper.check_consumer_tokens('Foursquare',
                                                     kwargs['fq_key'],
                                                     kwargs['fq_secret']):

                dbwrapper.insert_service_data('Foursquare',
                                               kwargs['fq_key'],
                                               kwargs['fq_secret'])
                successfull.append('Foursquare')
            else:
                unsuccessfull.append('Foursquare')

            if servicewrapper.check_consumer_tokens('Facebook',
                                                     kwargs['fb_app_id'],
                                                     kwargs['fb_app_secret']):

                dbwrapper.insert_service_data('Facebook',
                                               kwargs['fb_app_id'],
                                               kwargs['fb_app_secret'])
                successfull.append('Facebook')
            else:
                unsuccessfull.append('Facebook')

            self._show_services = False

            return 'Successfully added: %s, failed: %s' % (successfull, unsuccessfull)

        else:

            return 'Error.'


    add_services.exposed = True

    def oauth_dance(self, **kwargs):
        """ Performs oauth dance for the supported services
            with helper functions located in servicewrapper.
        """

        if len(kwargs) != 0:
            self._services.update(kwargs)

        if 'user' in self._services:
            authtoken = dbwrapper.add_user(self._services['user'])
            cherrypy.session['tokens'] = {}
            cherrypy.session['tokens']['user'] = self._services['user']
            cherrypy.session['tokens']['authtoken'] = authtoken
            if 'user' in self._services: del self._services['user']
            cherrypy.lib.sessions.save()

        if len(self._services['Twitter']) > 1:

            url, key, secret = servicewrapper.twitter_get_oauth_url(self._callback_url)

            cherrypy.session['tokens']['twitter_key'] = key
            cherrypy.session['tokens']['twitter_secret'] = secret
            raise cherrypy.HTTPRedirect(url)

        if len(self._services['Foursquare']) > 1:

            url = servicewrapper.foursquare_get_oauth_url(self._callback_url)
            raise cherrypy.HTTPRedirect(url)

        if len(self._services['Facebook']) > 1:

            app_id, temp = dbwrapper.get_service_tokens('Facebook')
            args = dict(client_id=app_id, redirect_uri=self._callback_url, scope='publish_actions,publish_stream')

            raise cherrypy.HTTPRedirect("https://www.facebook.com/dialog/oauth?" + urllib.urlencode(args))

        raise cherrypy.InternalRedirect('success')

    oauth_dance.exposed = True

    def success(self, *args, **kwargs):
        """ Redirects from external services return here one by one.
            If tokens are verified and fetched successfully,
            user data will be added and updated accordingly.
        """

        parameters = cherrypy.request.params

        if len(self._services['Twitter']) > 1:

            self._services['Twitter'] = ''
            self._statuses['twt'] = servicewrapper.twitter_save_access_token(cherrypy.session['tokens']['authtoken'],
                                                                             cherrypy.session['tokens']['twitter_key'],
                                                                             cherrypy.session['tokens']['twitter_secret'],
                                                                             parameters['oauth_verifier'])
            raise cherrypy.InternalRedirect('oauth_dance')

        if len(self._services['Foursquare']) > 1:

            self._services['Foursquare'] = ''
            self._statuses['fq'] = servicewrapper.foursquare_save_access_token(cherrypy.session['tokens']['authtoken'],
                                                                               parameters['code'],
                                                                               self._callback_url)
            raise cherrypy.InternalRedirect('oauth_dance')

        if len(self._services['Facebook']) > 1:

            self._services['Facebook'] = ''
            self._statuses['fb'] = servicewrapper.facebook_save_access_token(cherrypy.session['tokens']['authtoken'],
                                                      parameters['code'],
                                                      self._callback_url)
            raise cherrypy.InternalRedirect('oauth_dance')


        data = dbwrapper.get_user_data(cherrypy.session['tokens']['authtoken'])
        del cherrypy.session['tokens']

        return 'Added user %s. <br />Secret token (save this): <b>%s</b><br />\
                Facebook: %s, Twitter: %s, Foursquare: %s' % (data[1], data[2],
                                                              self._statuses['fb'],
                                                              self._statuses['twt'],
                                                              self._statuses['fq'])
    success.exposed = True


root = ArduBreathalyzer()
root.api = API()
cherrypy.tree.mount(root, '/')

conf = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(os.environ.get('PORT', '5000'))
    },
    '/': {
        'tools.sessions.on': True,
         'tools.sessions.timeout': 60
    },
    '/api': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
    }
}

cherrypy.config.update({'log.screen': True})

dbwrapper.create_tables()
cherrypy.quickstart(root, '/', conf)
