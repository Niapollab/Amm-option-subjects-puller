from dataclasses import dataclass
from moodle.constants import MOODLE_BASE_ADDRESS
from moodle.exceptions.IncorrectCredentialsError import IncorrectCredentialsError
# from moodle.session import MoodleSession
import requests as req
import re
import json

@dataclass(frozen=True)
class MoodleCredentials:
    '''Class to store Moodle login credentials.'''

    login: str
    '''The username for logging into Moodle.'''

    password: str
    '''The password for logging into Moodle.'''


@dataclass(frozen=True)
class MoodleCachedSession:
    '''Class to store a cached Moodle session.'''
    session_key: str
    moodle_session_cookie: str
    ...


async def authorize(credentials: MoodleCredentials) -> MoodleCachedSession:
    '''Authorize the user and create a new Moodle session.

    Args:
        credentials (MoodleCredentials): The login credentials for Moodle.

    Returns:
        MoodleSession: An authenticated Moodle session.
    '''

    # TODO: Build cached session there
    ...
    authPreparationResponse = req.get(f'{MOODLE_BASE_ADDRESS}/login/index.php')
    loginToken=_get_auth_preparation_token(authPreparationResponse.text)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'achor': '',
        'logintoken': loginToken,
        'username': credentials.login,
        'password': credentials.password
    }

    try:
        authResponse = req.post(f'{MOODLE_BASE_ADDRESS}/login/index.php',
                        cookies=authPreparationResponse.cookies, headers=headers, data=data)
    except req.exceptions.ConnectionError:
        # TO DO handle request errors
        ...
        
    _check_for_invalid_credentials(authResponse.text)
    cached_session=MoodleCachedSession(_get_api_token_key(authResponse.text), authResponse.history[0].cookies['MoodleSession'])
    await serialize_session("auth.json", cached_session)
    #TO DO fix circular import for returning MoodleSession
    return cached_session


async def restore(filename: str) -> MoodleCachedSession:
    '''Restore a Moodle session from a cached session file.

    Args:
        filename (str): The path to the file containing the cached session.

    Returns:
        MoodleSession: A restored Moodle session.
    '''
    try:
        with open(filename,"r") as file:
            auth_json=json.load(file)
            session_key=auth_json["session_key"]
            moodle_session_cookie=auth_json["moodle_session_cookie"]
            file.close()
        cached_session=MoodleCachedSession(session_key,moodle_session_cookie)
        #TO DO fix circular import for returning MoodleSession
        return cached_session
    except:
         raise Exception("Problem with restoring session from file")

async def serialize_session(filename: str, session:MoodleCachedSession):
    '''Read session from a cached session file.

    Args:
        filename (str): The path to the file containing the cached session.

    Returns:
        MoodleSession: A restored Moodle session.
    '''
    auth_info= {
        "session_key": session.session_key,
        "moodle_session_cookie": session.moodle_session_cookie
    }
    try:
        with open(filename,"w") as file:
            json_object=json.dumps(auth_info)
            file.write(json_object)
            file.close()
    except:
         raise Exception("Problem with serialization session to file")

def _get_api_token_key(html: str) -> str:
    match = re.search(r'<(?:.*?)name="sesskey"(?:.*?)value="(.*?)">', html)

    if not match:
        raise ValueError('Unable to get session token.')

    return match[1]

def _check_for_invalid_credentials(html: str) -> None:
    match = re.search(r'<a href="#" id="loginerrormessage"', html)
    if match:
        raise IncorrectCredentialsError('Invald credentials')
    
def _get_auth_preparation_token(html: str) -> str:
    match = re.search(
        r'<(?:.*?)name="logintoken"(?:.*?)value="(.*?)">', html)
    
    if not match:
                raise ValueError('Unable to get login token.')
    return match[1]