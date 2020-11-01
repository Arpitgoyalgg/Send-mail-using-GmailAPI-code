import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os



from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools




SCOPES = "https://mail.google.com/"
SERVICE_GMAIL = None
EMAIL_ADDRESS = False
LOGGED_IN = False


def init(userId="me", tokenFile="token.json", credentialsFile="credentials.json", _raiseException=True):

    global SERVICE_GMAIL, EMAIL_ADDRESS, LOGGED_IN


    EMAIL_ADDRESS = False
    LOGGED_IN = False

    try:
        store = file.Storage(tokenFile)
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(credentialsFile, SCOPES)
            creds = tools.run_flow(flow, store)
        SERVICE_GMAIL = build("gmail", "v1", http=creds.authorize(Http()))
        EMAIL_ADDRESS = SERVICE_GMAIL.users().getProfile(userId=userId).execute()["emailAddress"]
        LOGGED_IN = bool(EMAIL_ADDRESS)

        return EMAIL_ADDRESS
    except:
        if _raiseException:
            raise
        else:
            return False


def _createMessage(sender, recipient, subject, body, cc=None, bcc=None, mimeSubtype="plain", _threadId=None):

    message = MIMEText(body, mimeSubtype)
    message["to"] = recipient
    message["from"] = sender
    message["subject"] = subject
    if cc is not None:
        message["cc"] = cc
    if bcc is not None:
        message["bcc"] = bcc

    rawMessage = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")}
    if _threadId is not None:
        rawMessage['threadId'] = _threadId
    return rawMessage


def _createMessageWithAttachments(sender, recipient, subject, body, attachments, cc=None, bcc=None, mimeSubtype="plain", _threadId=None):

    message = MIMEMultipart()
    message["to"] = recipient
    message["from"] = sender
    message["subject"] = subject
    if cc is not None:
        message["cc"] = cc
    if bcc is not None:
        message["bcc"] = bcc

    messageMimeTextPart = MIMEText(body, mimeSubtype)
    message.attach(messageMimeTextPart)

    if isinstance(attachments, str):
        attachments = [attachments]  # If it's a string, put ``attachments`` in a list.

    for attachment in attachments:
        # Check that the file exists.
        content_type, encoding = mimetypes.guess_type(attachment)

        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)

        if main_type == "text":
            fp = open(attachment, "r")
            mimePart = MIMEText(fp.read(), _subtype=sub_type)
        else:
            fp = open(attachment, "rb")
            if main_type == "image":
                mimePart = MIMEImage(fp.read(), _subtype=sub_type)
            elif main_type == "audio":
                mimePart = MIMEAudio(fp.read(), _subtype=sub_type)
            else:
                mimePart = MIMEBase(main_type, sub_type)
                mimePart.set_payload(fp.read())
        fp.close()

        filename = os.path.basename(attachment)
        mimePart.add_header("Content-Disposition", "attachment", filename=filename)
        message.attach(mimePart)

    rawMessage = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")}
    if _threadId is not None:
        rawMessage['threadId'] = _threadId
    return rawMessage


def _sendMessage(message, userId="me"):

    message = SERVICE_GMAIL.users().messages().send(userId=userId, body=message).execute()
    return message


def send(recipient, subject, body, attachments=None, sender=None, cc=None, bcc=None, mimeSubtype="plain", _threadId=None):

    if SERVICE_GMAIL is None:
        init()

    if sender is None:
        sender = EMAIL_ADDRESS

    if attachments is None:
        msg = _createMessage(sender, recipient, subject, body, cc, bcc, mimeSubtype, _threadId=_threadId)
    else:
        msg = _createMessageWithAttachments(sender, recipient, subject, body, attachments, cc, bcc, mimeSubtype, _threadId=_threadId)
    _sendMessage(msg)
