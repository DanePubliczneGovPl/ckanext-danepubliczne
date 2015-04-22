import smtplib
import logging
from time import time
from email.mime.text import MIMEText
from email.header import Header
from email import Utils

from pylons import config
import ckan.lib.base as base
import ckan.lib.app_globals as app_globals
import ckan.lib.mailer as mailer
import ckan.logic as logic
from pylons import config
import paste.deploy.converters
import ckan
import ckan.lib.helpers as h
from ckan.common import _, g


log = logging.getLogger(__name__)

c = base.c
request = base.request
_ = base._


class FeedbackController(base.BaseController):
    @classmethod
    def get_form_items(cls):
        items = [
            {'name': 'feedback', 'control': 'textarea', 'label': _('Your feedback'),
             'placeholder': _('What is your feedback on this dataset?'), 'required': True},
            {'name': 'email', 'control': 'input', 'label': _('Email'),
             'placeholder': _('Leave email if we should get back to you')},
        ]
        return items

    def data_feedback(self):
        data = request.POST
        if not data.get('source_type') in ['dataset'] or not data.get('source_id'):
            base.abort(400)

        type = data['source_type']
        source_id = data['source_id']
        source_url = h.url_for(type + '_read', id=source_id, qualified=True)

        feedback = data.get('feedback', '').strip()
        email = data.get('email', '').strip()

        if not feedback:
            h.flash_error(_('Please provide your feedback'))
            h.redirect_to(source_url)

        if type == 'dataset':
            pkg = logic.get_action('package_show')({}, {'id': source_id})
        else:
            base.abort(400)

        msg = get_feedback_body(feedback, pkg, source_url, email)
        subject = _('User feedback concerning') + ' ' + pkg['title']

        rev = logic.get_action('revision_show')({}, {'id': pkg['revision_id']})
        # pkg.organization.name

        author = logic.get_action('user_show')({'user': g.site_id}, {'id': rev['author']})
        # pkg.creator_user_id
        # pkg.maintainer_email
        mail_from = config.get('smtp.mail_from')

        _mail_recipient(author['fullname'], author['email'], g.site_title, g.site_url, subject, msg,
                        cc={mail_from: None})
        # mailer.mail_recipient(author['display_name'], author['email'], subject, msg)

        h.flash_success(_('Thank you for your feedback!'))
        h.redirect_to(source_url)

    def new_dataset_feedback(self):
        data = request.POST
        if not data.get('came_from'):
            base.abort(400)

        source_url = data['came_from']

        feedback = data.get('feedback', '').strip()
        email = data.get('email', '').strip()

        if not feedback:
            h.flash_error(_('Please provide your feedback'))
            h.redirect_to(str(source_url))

        msg = get_new_dataset_feedback_body(feedback, email)
        subject = _('Proposition for new dataaset')

        mail_from = config.get('smtp.mail_from')

        _mail_recipient(g.site_title, mail_from, g.site_title, g.site_url, subject, msg)

        h.flash_success(_('Thank you for your feedback!'))
        h.redirect_to(str(source_url))

    def reset_config(self):
        if 'cancel' in request.params:
            h.redirect_to(controller='admin', action='config')

        if request.method == 'POST':
            # remove sys info items
            for item in self._get_config_form_items():
                name = item['name']
                app_globals.delete_global(name)
            # reset to values in config
            app_globals.reset()
            h.redirect_to(controller='admin', action='config')

        return base.render('admin/confirm_reset.html')

    def config(self):

        items = self._get_config_form_items()
        data = request.POST
        if 'save' in data:
            # update config from form
            for item in items:
                name = item['name']
                if name in data:
                    app_globals.set_global(name, data[name])
            app_globals.reset()
            h.redirect_to(controller='admin', action='config')

        data = {}
        for item in items:
            name = item['name']
            data[name] = config.get(name)

        vars = {'data': data, 'errors': {}, 'form_items': items}
        return base.render('admin/config.html',
                           extra_vars=vars)


def get_new_dataset_feedback_body(feedback, email=''):
    body = _(
        "User {email} has sent proposition for a new dataset:\n"
        "\n"
        "{feedback}\n"
    )

    d = {
        'feedback': feedback,
        'email': email
    }
    return body.format(**d)


def get_feedback_body(feedback, pkg_dict, source_url, email=''):
    body = _(
        "User {email} has sent feedback concerning {display_name}[{url}].\n"
        "\n"
        "Feedback:\n"
        "\n"
        "{feedback}\n"
    )

    d = {
        'feedback': feedback,
        'display_name': pkg_dict['title'],
        'url': source_url,
        'email': email
    }
    return body.format(**d)


def _mail_recipient(recipient_name, recipient_email,
                    sender_name, sender_url, subject,
                    body, headers={}, cc={}):
    mail_from = config.get('smtp.mail_from')
    # body = add_msg_niceties(recipient_name, body, sender_name, sender_url)

    msg = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
    for k, v in headers.items(): msg[k] = v
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _("%s <%s>") % (sender_name, mail_from)
    recipient = u"%s <%s>" % (recipient_name, recipient_email)
    msg['To'] = Header(recipient, 'utf-8')

    ccs = []
    for mail, name in cc.iteritems():
        if name:
            ccs.append(u"%s <%s>" % (name, mail))
        else:
            ccs.append(mail)
    if ccs:
        msg['CC'] = Header(', '.join(ccs), 'utf-8')
    msg['Date'] = Utils.formatdate(time())
    msg['X-Mailer'] = "CKAN %s" % ckan.__version__

    # Send the email using Python's smtplib.
    smtp_connection = smtplib.SMTP()
    if 'smtp.test_server' in config:
        # If 'smtp.test_server' is configured we assume we're running tests,
        # and don't use the smtp.server, starttls, user, password etc. options.
        smtp_server = config['smtp.test_server']
        smtp_starttls = False
        smtp_user = None
        smtp_password = None
    else:
        smtp_server = config.get('smtp.server', 'localhost')
        smtp_starttls = paste.deploy.converters.asbool(
            config.get('smtp.starttls'))
        smtp_user = config.get('smtp.user')
        smtp_password = config.get('smtp.password')
    smtp_connection.connect(smtp_server)
    try:
        #smtp_connection.set_debuglevel(True)

        # Identify ourselves and prompt the server for supported features.
        smtp_connection.ehlo()

        # If 'smtp.starttls' is on in CKAN config, try to put the SMTP
        # connection into TLS mode.
        if smtp_starttls:
            if smtp_connection.has_extn('STARTTLS'):
                smtp_connection.starttls()
                # Re-identify ourselves over TLS connection.
                smtp_connection.ehlo()
            else:
                raise mailer.MailerException("SMTP server does not support STARTTLS")

        # If 'smtp.user' is in CKAN config, try to login to SMTP server.
        if smtp_user:
            assert smtp_password, ("If smtp.user is configured then "
                                   "smtp.password must be configured as well.")
            smtp_connection.login(smtp_user, smtp_password)

        smtp_connection.sendmail(mail_from, [recipient_email], msg.as_string())
        log.info("Sent email to {0}".format(recipient_email))

    except smtplib.SMTPException, e:
        msg = '%r' % e
        log.exception(msg)
        raise mailer.MailerException(msg)
    finally:
        smtp_connection.quit()