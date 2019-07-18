#!/usr/bin/python3
import re
from joblib import Memory
import requests
from lxml import html
from collections import OrderedDict
from jinja2 import Template
import sh
import os
from pprint import pprint
from argparse import ArgumentParser

memory = Memory('./cachedir', verbose=0)

@memory.cache
def get_pypi_package_page(name):
    r = requests.get("https://pypi.org/project/%s/" % (name))
    r.raise_for_status()
    return r

def get_pypi_parsed(name):
    r = get_pypi_package_page(name)
    x = html.fromstring(r.content)
    return x

def get_pypi_name(name):
    special_names = {
        'flask-oslolog': 'flask_oslolog',
    }
    x = get_pypi_parsed(name)
    real_name = ''.join(x.xpath('(//h1)[1]/text()'))
    real_name = real_name.strip()
    split_title = real_name.split(' ', 2)
    if len(split_title) > 2:
        raise IndexError("there is more than 1 space in the name. split: %s presplit: %s input: %s" % (split_title, real_name, name))
    real_name = split_title[0]
    return real_name

def get_pypi_links(name):
    x = get_pypi_parsed(name)
    selectors = [
        '//a[text()[contains(.,"Source Code")]]/@href',
        # very few occurances
        '//a[text()[contains(.,"Source")]]/@href',
        '//a[text()[contains(.,"Homepage")]]/@href',
        # FIXME also read in the rest
    ]
    links = [link for s in selectors for link in x.xpath(s)]
    links = list(OrderedDict.fromkeys(links))
    # FIXME upstream links
    # FIXME try importing other SCM to git
    # FIXME try to use the pypi tar for projects that are not in git
    manual = {
        'pykerberos': 'https://github.com/02strich/pykerberos',
        'sphinxcontrib-htmlhelp': 'https://github.com/sphinx-doc/sphinxcontrib-htmlhelp',
        'sphinxcontrib-serializinghtml': 'https://github.com/sphinx-doc/sphinxcontrib-serializinghtml',
        'sphinxcontrib-qthelp': 'https://github.com/sphinx-doc/sphinxcontrib-qthelp',
        'sphinxcontrib-devhelp': 'https://github.com/sphinx-doc/sphinxcontrib-devhelp',
        'sphinxcontrib-applehelp': 'https://github.com/sphinx-doc/sphinxcontrib-applehelp',
        'waiting': 'https://github.com/vmalloc/waiting',
        'capacity': 'https://github.com/vmalloc/capacity',
        'sentinels': 'https://github.com/vmalloc/sentinels',
        'rsa': 'https://github.com/sybrenstuvel/python-rsa/',
        'WebOb': 'https://github.com/Pylons/webob',
        'Routes': 'https://github.com/bbangert/routes',
        'typing': 'https://github.com/python/typing',
        'uwsgi': 'https://github.com/unbit/uwsgi',
        'PasteDeploy': 'https://github.com/Pylons/pastedeploy',
        'docopt': 'http://github.com/docopt/docopt',
        'python-ldap': 'https://github.com/python-ldap/python-ldap',
        'ryu': 'https://github.com/osrg/ryu',
        'pytest': 'https://github.com/pytest-dev/pytest/',
        'lxml': 'https://github.com/lxml/lxml',
        'certifi': 'https://github.com/certifi/python-certifi',
        'django-appconf': 'https://github.com/django-compressor/django-appconf',
        'alabaster': 'https://github.com/bitprophet/alabaster',
        'rcssmin': 'https://github.com/ndparker/rcssmin',
        'grpcio': 'https://github.com/grpc/grpc',
        'fixtures': 'https://github.com/testing-cabal/fixtures',
        'nose': 'https://github.com/nose-devs/nose',
        'Mako': 'https://github.com/sqlalchemy/mako',
        'psycopg2': 'https://github.com/psycopg/psycopg2',
        'Pillow': 'https://github.com/python-pillow/Pillow',
        # this is a fork, there is still the original hg repo https://bitbucket.org/ianb/tempita/
        'Tempita': 'https://github.com/gjhiggins/tempita',
        'ply': 'https://github.com/dabeaz/ply',
        # this is a fork, there is still the original hg repo https://bitbucket.org/jurko/suds/
        'suds-jurko': 'https://github.com/suds-community/suds',
        'requests-toolbelt': 'https://github.com/requests/toolbelt/',
        'pyOpenSSL': 'https://github.com/pyca/pyopenssl/',
        'mypy-extensions': 'https://github.com/python/mypy_extensions',
        'MarkupSafe': 'https://github.com/pallets/markupsafe',
        'thrift': 'https://github.com/apache/thrift',
        'pypowervm': 'https://github.com/powervm/pypowervm',
        'arrow': 'https://github.com/crsmithdev/arrow',
        'gnocchiclient': 'https://github.com/gnocchixyz/python-gnocchiclient',
        'pyudev': 'https://github.com/pyudev/pyudev',
        'eventlet': 'https://github.com/eventlet/eventlet',
        'kazoo': 'https://github.com/python-zk/kazoo',
        'SQLAlchemy': 'https://github.com/sqlalchemy/sqlalchemy',
        'python-subunit': 'https://github.com/testing-cabal/subunit',
        'urllib3': 'https://github.com/urllib3/urllib3',
        'mock': 'https://github.com/testing-cabal/mock',
        'tornado': 'https://github.com/tornadoweb/tornado',
        'ovs': 'https://github.com/openvswitch/ovs',
        # import of bzr repo
        'beautifulsoup4': 'https://github.com/JanZerebecki/beautifulsoup',
        'pycryptodomex': 'https://github.com/Legrandin/pycryptodome',
        'pylxd': 'https://github.com/lxc/pylxd',
        'requests-mock': 'https://github.com/jamielennox/requests-mock',
        # import of hg repo
        'anyjson': 'https://github.com/JanZerebecki/anyjson',
        # import of hg repo https://hg.python.org/unittest2
        'unittest2': 'https://github.com/garbas/unittest2',
        'gunicorn': 'https://github.com/benoitc/gunicorn',
        'django-compressor': 'https://github.com/django-compressor/django-compressor',
        'python-3parclient': 'https://github.com/hpe-storage/python-3parclient',
        'asyncio': 'https://github.com/python/asyncio',
        'sphinxcontrib-jsmath': 'https://github.com/sphinx-doc/sphinxcontrib-jsmath',
        'requests': 'https://github.com/kennethreitz/requests',
        'Jinja2': 'https://github.com/pallets/jinja',
        # import of hg https://bitbucket.org/ruamel/yaml/
        'ruamel.yaml': 'https://github.com/gschizas/ruamel-yaml',
        'mpmath': 'https://github.com/fredrik-johansson/mpmath',
        # import of hg https://bitbucket.org/ecollins/passlib
        'passlib': 'https://github.com/JanZerebecki/passlib',
        'joblib': 'https://github.com/joblib/joblib',
        'dnspython3': 'https://github.com/rthalley/dnspython',
        # this is a fork, there doesn't appear to be any scm for the pypi package
        'termcolor': 'https://github.com/hfeeki/termcolor',
        'nwdiag': 'https://github.com/blockdiag/nwdiag',
        'uritemplate': 'https://github.com/python-hyper/uritemplate',
        'importlib-metadata': 'https://gitlab.com/python-devs/importlib_metadata',
        'pycrypto': 'https://github.com/dlitz/pycrypto',
        'mypy': 'https://github.com/python/mypy',
   }
    if name in manual:
        links.append(manual[name])
    return links

def get_pypi_maintainers(name):
    x = get_pypi_parsed(name)
    users = [user for user in x.xpath('//*[@class = "sidebar-section__maintainer"]/a/@href')]
    return users

def create_package(pypi_name, version, url, git_url):
    obs_name = 'python-%s-source' %pypi_name
    try:
        create_package_(pypi_name, version, url, git_url)
    except:
        print('exception, deleting: ', obs_name)
        sh.rm('-rf', obs_name)
        sh.osc('rm', obs_name)

def create_package_(pypi_name, version, url, git_url):
    obs_name = 'python-%s-source' %pypi_name
    #if os.path.isdir(obs_name):
    #    print('skipping', obs_name, git_url)
    #    return
    args = {'pypi_name': pypi_name, 'obs_name': obs_name, 'version': version, 'url': url, 'git_url': git_url}
    print(obs_name, version, git_url)
    sh.osc('mkpac', obs_name, _ok_code=[0, 1])
    # FIXME rsa can only sdist on python2
    # FIXME thrift has entrypoint at lib/py/setup.py
    # FIXME ovs has entrypoint at python/setup.py
    template = Template(open('create-packages-from-pip.spec.j2').read())
    content = template.render(args)
    open('{0}/{0}.spec'.format(obs_name), 'w').write(content)
    sh.osc('add', '{0}/{0}.spec'.format(obs_name))
    template = Template(open('create-packages-from-pip.changes.j2').read())
    content = template.render(args)
    open('{0}/{0}.changes'.format(obs_name), 'w').write(content)
    sh.osc('add', '{0}/{0}.changes'.format(obs_name))
    git_dir = '{0}/{1}'.format(obs_name, pypi_name)
    if not os.path.isdir(git_dir):
        sh.git('-C', obs_name, 'clone', git_url, pypi_name)
        git_version = version
        special_version = {
            'flask_oslolog': {'0.1': 'master'},
            'openstack.nose_plugin': {'0.11': 'a1037419eff17e7a8c788e6d3051c00151154c31'},
            'enum-compat': {None: '0.0.2'},
            'uWSGI': {None: '2.0.18'},
            'rtslib-fb': {'2.1.69': 'v2.1.fb69'},
            'certifi': {'2019.6.16': '2019.06.16'},
            'requests-aws': {'0.1.8': '2181a74fcffc591dcc310346973475ae3a514f01'},
            'XStatic-angular-ui-router': {'0.3.1.2': 'd9b95b7ca2ad9ee603cf9457a364d780f680b8d5'},
            # FIXME make a reimport from original hg or reconstruct from pypi as the below is not quite right
            'Tempita': {'0.5.2': 'f9ac35a24fb2b9215663cbd7a7b4b6e26c0eacf7'},
            # FIXME reverse from pypi tar as git repo doesn't have the newer tag nor versions in history
            'gnocchiclient': {'7.0.5': '7.0.4'},
            'frozendict': {'1.2': '7566f29882ea42d10e46d0915f817c6c15b6de7d'},
            'beautifulsoup4': {'4.7.1': '0c1053d9ae093ea7db74c24ee29f430cc6fcae88'},
            'python-3parclient': {'4.2.9': '23200ddcbb41334c92df33eeaf5174eb79982d1a'},
            'XStatic-Hogan': {'2.0.0.2': '9e39977f6a6744810b08fa0323147e9f31dbd363'},
            'sphinxcontrib-serializinghtml': {'1.1.3': '422d9a5fbf748faa18d425d2e07167ece56fa245'},
            'snowballstemmer': {'1.9.0': '69ea0d05cdb5aeb073015912cf8e1d18e1d645a4'},
            'XStatic-JQuery-Migrate': {'1.2.1.1': '989b3b31106727542dd83810c3b952f90d8cdb8f'},
            'google-auth-httplib2': {'0.0.3': '73ca3ddd2a340128eb3a4109a8e7130fc1a07aef'},
            'XStatic-JQuery.quicksearch': {'2.0.3.1': 'f5221c8c30507340846d97d6db41a782e7c63316'},
        }
        if pypi_name in special_version and version in special_version[pypi_name]:
            git_version = special_version[pypi_name][version]
        version_formats = {
            '{0}',
            'v{0}',
            'version-{0}',
            'release-{0}',
            'release_{0}',
            'release_v{0}',
            '{1}-{0}',
            'underscore-for-dash',
            'rel_underscore-for-dash',
        }
        for version_format in version_formats:
            test_version = version_format.format(git_version, pypi_name)
            if version_format is 'underscore-for-dash':
                test_version = re.sub('[.]', '_', git_version)
            elif version_format is 'rel_underscore-for-dash':
                test_version = 'rel_' + re.sub('[.]', '_', git_version)
            status = sh.git('-C', git_dir, 'rev-parse', test_version, _ok_code=[0, 128])
            if 0 == status.exit_code:
                git_version = test_version
                break
        sh.git('-C', git_dir, 'checkout', '-b', version, git_version)
        # osc add for the git repo needs to run with cwd in the package, it doesn't work with cwd in the project
        sh.osc('add', pypi_name, _cwd=obs_name, _in='y\n')

def main():
    parser = ArgumentParser()
    parser.add_argument('pypi_name', nargs='?', help='only run for package matching pypi-name')
    args = parser.parse_args()
    for requirement in open('pip-requirements.txt'):
        requirement = requirement.strip()
        match = re.match('^(?P<name>[^=]*)(?:(?:===)(?P<version>[^;]*)(?:(?:;)(?:python_version==\'[.0-9]+\')?)?)?$', requirement)
        if args.pypi_name and not args.pypi_name in match.group('name'):
            continue
        name_input = match.group('name')
        name_regex = '^[a-zA-Z0-9._-]+$'
        if not re.match(name_regex, name_input):
            raise ValueError("name_input contains disallowed chars. regex: %s value: %s" % (name_regex, name_input))
        # FIXME this still doesn't always work, e.g. a - sometimes is a _ in the sdist
        name = get_pypi_name(name_input)
        if not re.match(name_regex, name_input):
            raise ValueError("name contains disallowed chars. regex: %s value: %s" % (name_regex, name))
        version = match.group('version')
        if not ( version is None or re.match(name_regex, version) ):
            raise ValueError("version contains disallowed chars. regex: %s value: %s" % (name_regex, version))
        links = get_pypi_links(name_input)
        maintainers = get_pypi_maintainers(name_input)
        special_git_urls = {
            'openstack.nose_plugin': 'https://review.opendev.org/openstack/openstack-nose',
            'nosehtmloutput': 'https://review.opendev.org/openstack/nose-html-output',
            'PrettyTable': 'https://github.com/lmaurits/prettytable',
            'XStatic-jQuery': 'https://github.com/xstatic-py/xstatic-jquery',
            'XStatic-objectpath': 'https://github.com/mike-marcacci/objectpath',
            'python-hnvclient': 'https://review.opendev.org/x/python-hnvclient',
            'python-kingbirdclient': 'https://review.opendev.org/x/python-kingbirdclient',
            'cursive': 'https://review.opendev.org/x/cursive',
            'os-xenapi': 'https://review.opendev.org/x/os-xenapi',
            'rsd-lib': 'https://review.opendev.org/x/rsd-lib',
            'doc8': 'https://review.opendev.org/x/doc8',
            'pyghmi': 'https://review.opendev.org/x/pyghmi',
            'fixtures-git': 'https://review.opendev.org/x/fixtures-git',
            'zuul-sphinx': 'https://review.opendev.org/zuul/zuul-sphinx',
            'libvirt-python': 'https://libvirt.org/git/libvirt-python.git',
        }
        git_url = ''
        if name in special_git_urls:
            git_url = special_git_urls[name]
        elif '/user/openstackci/' in maintainers:
            if name.startswith('openstack-'):
                git_url = 'https://review.opendev.org/openstack/%s' % re.sub('^openstack-', '', name)
            else:
                git_url = 'https://review.opendev.org/openstack/%s' % name.lower()
        else:
            # FIXME try probing links for SCM support
            for link in links:
                git_match = re.match('^https?://(?P<host>github\.com|gitlab\.com)/(?P<group>[^/]+)/(?P<repo>[^/]+)/?$', link)
                if not git_match:
                    continue
                repo = re.sub('.git$', '', git_match.group('repo'))
                git_url = "https://%s/%s/%s.git" % (git_match.group('host'), git_match.group('group'), repo)
                break
        if not git_url:
            print( KeyError("no git url to clone found. input: %s name: %s links: %s" % (name_input, name, links)) )
            continue
        git_url_regex = '^[^%]+$'
        if not re.match(git_url_regex, git_url):
            raise ValueError("git_url contains disallowed chars. regex: %s value: %s" % (git_url_regex, git_url))
        if len(links) <= 0:
            links.append(git_url)
        link = links[0]
        if not re.match(git_url_regex, link):
            raise ValueError("link contains disallowed chars. regex: %s value: %s" % (git_url_regex, link))
        create_package(name, version, link, git_url)

main()
