# -*- coding: utf-8 -*-

from facepy import GraphAPI
import foursquare
import tweepy
import dbwrapper
import cgi
import urllib


def check_consumer_tokens(service, key, secret):

    if key != '' and secret != '':

        if service == 'Twitter':
            auth = tweepy.OAuthHandler(str(key), str(secret))
            try:
                auth.get_authorization_url()
                return True
            except:
                pass

        if service == 'Foursquare':
            client = foursquare.Foursquare(str(key), str(secret))
            try:
                client.oauth.auth_url()
                return True
            except:
                pass

        if service == 'Facebook':
            return True

    return False

def twitter_get_oauth_url(callback_url):

    consumer_token, consumer_secret = dbwrapper.get_service_tokens('Twitter')
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret, callback_url)

    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        return False

    return redirect_url, auth.request_token.key, auth.request_token.secret

def twitter_save_access_token(authtoken, key, secret, verifier):

    auth = tweepy.OAuthHandler(key, secret)
    auth.set_request_token(key, secret)

    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError:
        return False

    dbwrapper.update_user(authtoken,
                       tw_key=auth.access_token.key,
                       tw_secret=auth.access_token.secret)
    return True

def facebook_save_access_token(authtoken, code, callback_url):

    app_id, secret = dbwrapper.get_service_tokens('Facebook')

    args = dict(client_id=app_id, redirect_uri=callback_url)
    args["client_secret"] = secret.strip()
    args["code"] = code
    url = "https://graph.facebook.com/oauth/access_token?" + urllib.urlencode(args)

    try:
        response = cgi.parse_qs(urllib.urlopen(url).read())
        access_token = response["access_token"][-1]
        dbwrapper.update_user(authtoken, fb_token=access_token)
        return True
    except:
        return False

def foursquare_get_oauth_url(callback_url):

    consumer_token, consumer_secret = dbwrapper.get_service_tokens('Foursquare')
    client = foursquare.Foursquare(consumer_token,
                                   consumer_secret,
                                   redirect_uri=unicode(callback_url))
    try:
        auth_uri = client.oauth.auth_url()
    except:
        print 'Error! Failed to get request token.'

    return auth_uri

def foursquare_save_access_token(authtoken, code, callback_url):

    try:
        consumer_token, consumer_secret = dbwrapper.get_service_tokens('Foursquare')
        client = foursquare.Foursquare(consumer_token,
                                       consumer_secret,
                                       callback_url)

        access_token = client.oauth.get_token(code)
        dbwrapper.update_user(authtoken, fq_token=access_token)
        return True
    except Exception as e:
        print e
        return False

def post(authtoken, bac, service, lat=None, lon=None):

    results = []

    print bac

    if service == 'all':

        for service in methods:
            results.append(methods[service](authtoken, bac, service, lat, lon))
        return results

    else:
        if service.lower() in methods:
            result = methods[service.lower()](authtoken, bac, service, lat, lon)
            return result
        else:
            return False

def facebook(authtoken, bac, service, lat, lon):

    data = dbwrapper.get_user_data(authtoken)
    try:
        graph = GraphAPI(data[5])

        if lat != None:

            page_id = graph.fql('SELECT page_id FROM place\
                                 WHERE distance(latitude, longitude, \"%s\", \"%s\") < 50\
                                 LIMIT 1' % (lat, lon))

            if len(page_id['data'][0]) != 0:
                graph.post('/me/feed', message='testi', retry=0, place=page_id['data'][0]['page_id'])
            else:
                graph.post('/me/feed', message='testi', retry=0)

        else:
            graph.post('/me/feed', message='testi', retry=0)

        return True
    except:
        return False

def twitter(authtoken, bac, service, lat, lon):

    key, secret = dbwrapper.get_service_tokens('Twitter')
    data = dbwrapper.get_user_data(authtoken)
    status = 'Promilleja veressä: %s ‰' % bac

    try:
        auth = tweepy.OAuthHandler(key, secret)
        auth.set_access_token(data[3], data[4])
        api = tweepy.API(auth)
        api.update_status(status=status, lat=str(lat), long=str(lon))
        return True
    except:
        return False

methods = {'facebook': facebook, 'twitter': twitter}