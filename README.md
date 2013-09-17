ArduBreathalyzerAPI
===================

API and social media wrapper for Arduino Breathalyzer. Scroll down for English version.

Mikä tämä on?
-------------
ArduBreathalyzerAPI on Pythonilla kirjoitettu karkea REST-rajapinta/web-sovellus, joka hoitaa kommunikaation Arduinoon pohjautuvan alkometrin sekä tietokannan ja sosiaalisen median välillä.

Projektin taustasta sekä koodista on juttu __[MikroPC](http://www.mikropc.net/) 9/2013__:ssa. Koodin toinen puoli eli Arduinon osuus löytyy reposta [ArduBreathalyzer](https://github.com/skvark/ArduBreathalyzer).

Toiminta
--------
Sovellus koostuu muutamasta eri osasta:

* *ArduBreathalyzerAPI.py*
  - CherryPylla toteutetun web-sovelluksen päätiedosto, joka sisältää muutaman luokan
  - `class ArduBreathalyzer(object)` toteuttaa sovelluksen etusivun ja palvelujen/käyttäjien lisäämiseen liittyvät asiat, jotka kaikki sijaitsevat sovelluksen juuressa
  - `class API(object)` toteuttaa itse REST-rajapinnan polussa api/, joka sallii vain GET- ja POST-pyynnöt
* *dbwrapper.py*
  - tiedosto sisältää tietokannan (PostgreSQL) kanssa tehtävät operaatiot: taulujen luominen, tietojen lisääminen, tietojen päivittäminen ja tietojen hakeminen
* *servicewrapper.py*
  - tiedostossa on toteutettuna Facebookin, Twitterin sekä Foursquaren kanssa kommunikointi valmiilla kirjastoilla 
  - moduulilla hoidetaan Oauthin vaatimia toimintoja ja esimerkiksi käyttäjien tilan päivitys tapahtuu tämän moduulin funktioilla

Tämän version pystyy ja se on __tarkoitus laittaa suoraan Herokuun__ pyörimään. Foursquare-sovelluksen voi lisätä rajapintaan, 
mutta käyttäjän sijainnin/tilan päivitystä ei ole ainakaan vielä toteutettu.

Riippuvuudet asentuvat automaattisesti `requirements.txt`-tiedoston mukaan pip:llä.

Rajapinnan pyynnöt
------------------

Kun rajapintaan on lisännyt haluttujen palvelujen sovellusten avaimet ja lisätty käyttäjä, rajapintaan voi lisätä ja hakea tietoa seuraavanlaisilla pyynnöillä:

__POST__

http://sovellus.herokuapp.com/api/käyttäjänimi/käyttäjän_avain/bac/palvelu/latitude/longitude

Parametrit:

- käyttäjänimi, pakollinen
- käyttäjän_avain: rajapinnan antama salainen avain, pakollinen
- bac: veren alkoholipitoisuus (desimaalit pisteellä eroteltuna, esim. 0.0), pakollinen
- palvelu: All, Facebook, Twitter, None, vapaaehtoinen
- latitude: latitude-koordinaatti, desimaalit pisteellä eroteltuna, ei pakollinen
- longitude: latitude-koordinaatti, desimaalit pisteellä eroteltuna, ei pakollinen

Tiedot lisätään aina tietokantaan, mutta ei lähetetä sosiaaliseen mediaan ellei niin ole määritelty. Kannasta tietoa voi hakea GETillä:

__GET__

http://sovellus.herokuapp.com/api/käyttäjänimi/vuosi/viikko/viikonpäivä

Käyttäjänimi ja vuosi ovat pakollisia, muut ovat vapaaehtoisia. Data palautuu JSON-formaatissa seuraavasti:

    [
      ‘käyttäjänimi’: {  
        ‘unix_timestamp’: {‘bac’: value, ‘lat’: value, ‘lon’: value},
        ‘unix_timestamp’: {‘bac’: value, ‘lat’: value, ‘lon’: value},
        ‘unix_timestamp’: {‘bac’: value, ‘lat’: value, ‘lon’: value},
      }
    ]

Sosiaalinen media ja sovellukset
--------------------------------

Jotta datan voi lähettää sosiaaliseen mediaan saakka, täytyy jokaiseen palveluun tehdä oma sovellus, jonka voi lisätä rajapintaan.

Rajapinta tukee Facebookia ja Twitteriä tilan päivittämiseen saakka. 
Foursquaren osalta vain sovelluksen linkitys on toteutettu eli Foursquareen ei voi lähettää dataa eteenpäin.

Kyseisten sovellusten avaimet on lisättävä sovelluksen etusivulla, kun se ensimmäisen kerran avataan.

Muuta huomioitavaa
------------------

Tarkempaa infoa löytyy MikroPC:n numerosta 9/2013. Tämä toteutus on karkea runko ja sitä on suotavaa parantaa. 

Rajapintaa ei ole tarkoitettu muuhun kuin hupikäyttöön. 
Älä luovuta rajapinnan osoitetta tai salaista avaintasi kenellekään, ellet tiedä tarkalleen mitä teet.

What is this?
-------------
ArduBreathalyzerAPI is a web application and REST API which communicates with Arduino based breathalyzer and social media.
It's implemented with Python and CherryPy (+PostgreSQL and some python social media modules). This version is meant to be run at Heroku.

You can found the sources for the Arduino part from [ArduBreathalyzer](https://github.com/skvark/ArduBreathalyzer).

The background story and more information about this project can be found from a Finnish IT magazine called __[MikroPC](http://www.mikropc.net/) (PC World Finland) 9/2013__.

How it works
------------
The app consists from the following parts:

* *ArduBreathalyzerAPI.py*
  - CherryPy classes and other stuff related to it
  - `class ArduBreathalyzer(object)` - index page and adding users/services
  - `class API(object)` can be found from path api/, only GET and POST requests work
* *dbwrapper.py*
  - PostgreSQL related stuff, database interaction
* *servicewrapper.py*
  - Social media stuff, Oauth and posting 


Dependencies will be installed with pip by `requirements.txt`.

API methods
-----------

After services and user has been added, following methods can be used:

__POST__

http://sovellus.herokuapp.com/api/user/kuser_token/bac/service/latitude/longitude

Parameters:

- username*
- user_token*: secret token which the app gives for every user
- bac*: blood alcohol content as a float
- service: All, Facebook, Twitter, None
- latitude: latitude coordinate as a float
- longitude: latitude coordinate as a float

__GET__

http://sovellus.herokuapp.com/api/user/year/week/weekday

All parameters are integers. API returns data in this format:

    [
      ‘username’: {  
        ‘unix_timestamp’: {‘bac’: value, ‘lat’: value, ‘lon’: value},
        ‘unix_timestamp’: {‘bac’: value, ‘lat’: value, ‘lon’: value},
        ‘unix_timestamp’: {‘bac’: value, ‘lat’: value, ‘lon’: value},
      }
    ]

Notes
-----
Do not give the API url to anyone and keep the secret tokens to yourself unless you know what you're doing.
