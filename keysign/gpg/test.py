#!/bin/bash/env python

import os
import sys
import shutil
import tempfile

import gpgme
import gpg

import unittest

from io import BytesIO
from StringIO import StringIO

__all__ = ['GpgTestSuite']

keydir = os.path.join(os.path.dirname(__file__), 'keys')
gpg_default = os.environ['HOME'] + '/.gnupg/'


class GpgTestSuite(unittest.TestCase):

    def keyfile(self, key):
        return open(os.path.join(keydir, key), 'rb')

    def test_gpg_set_engine(self):
        ctx = gpgme.Context()

        tmpdir = tempfile.mkdtemp(prefix='tmp.gpghome')
        gpg.gpg_set_engine(ctx, gpgme.PROTOCOL_OpenPGP, tmpdir)

        keys = [key for key in ctx.keylist()]

        self.assertEqual(len(keys), 0)
        self.assertEqual(ctx.protocol, gpgme.PROTOCOL_OpenPGP)

        # clean temporary dir
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_gpg_reset_engine(self):
        ctx = gpgme.Context()
        # set a temporary dir for gpg home
        tmpdir = tempfile.mkdtemp(prefix='tmp.gpghome')
        ctx.set_engine_info(gpgme.PROTOCOL_OpenPGP, gpg.gpg_path, tmpdir)

        # check if we have created the new gpg dir
        self.assertTrue(os.path.isdir(tmpdir))
        gpg.gpg_reset_engine(ctx, tmpdir, gpgme.PROTOCOL_OpenPGP)

        self.assertEqual(gpgme.PROTOCOL_OpenPGP, ctx.protocol)
        self.assertFalse(os.path.exists(tmpdir))

        # clean temporary dir
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_gpg_copy_secrets(self):
        ctx = gpgme.Context()
        tmpdir = tempfile.mkdtemp(prefix='tmp.gpghome')
        ctx.set_engine_info(gpgme.PROTOCOL_OpenPGP, gpg.gpg_path, tmpdir)

        gpg.gpg_copy_secrets(ctx, tmpdir)

        # get the user's secret keys
        default_ctx = gpgme.Context()
        default_ctx.set_engine_info(gpgme.PROTOCOL_OpenPGP, gpg.gpg_path, gpg_default)
        default_secret_keys = [key for key in default_ctx.keylist(None, True)]

        # compare the imported keys with the original secret keys
        secret_keys = [key for key in ctx.keylist(None, True)]

        self.assertEqual(len(secret_keys), len(default_secret_keys))
        i = 0
        for i in xrange(len(secret_keys)):
            self.assertEqual(secret_keys[i].subkeys[0].fpr, default_secret_keys[i].subkeys[0].fpr)
            i += 1
        # clean temporary dir
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_gpg_import_key_by_fpr(self):
        ctx = gpgme.Context()
        tmpdir = tempfile.mkdtemp(prefix='tmp.gpghome')
        ctx.set_engine_info(gpgme.PROTOCOL_OpenPGP, gpg.gpg_path, tmpdir)

        with self.keyfile('testkey1.pub') as fp:
            ctx.import_(fp)

        res = gpg.gpg_import_key_by_fpr(ctx, '31E91E906BA25D74BB315DEA9B33CFC7BB70DAFA')
        self.assertTrue(res)

        # can we get the key ?
        key = ctx.get_key('31E91E906BA25D74BB315DEA9B33CFC7BB70DAFA')
        # clean temporary dir
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_gpg_import_keydata(self):
        ctx = gpgme.Context()
        tmpdir = tempfile.mkdtemp(prefix='tmp.gpghome')
        ctx.set_engine_info(gpgme.PROTOCOL_OpenPGP, gpg.gpg_path, tmpdir)

        with self.keyfile('testkey1.pub') as fp:
            keydata = fp.read()

        res = gpg.gpg_import_keydata(ctx, keydata)
        self.assertTrue(res)

        # can we get the key ?
        key = ctx.get_key('john.doe@test.com')

    def test_gpg_sign_uid(self):
        ctx = gpgme.Context()
        tmpdir = tempfile.mkdtemp(prefix='tmp.gpghome')
        ctx.set_engine_info(gpgme.PROTOCOL_OpenPGP, gpg.gpg_path, tmpdir)

        with self.keyfile('testkey1.pub') as fp:
            ctx.import_(fp)

        userId = ctx.get_key('john.doe@test.com').uids[0]
        res = gpg.gpg_sign_uid(ctx, tmpdir, userId)
        self.assertTrue(res)

        # verify if we have the uid signed
        sigs = ctx.get_key('john.doe@test.com').uids[0].signatures
        self.assertEqual(len(sigs), 2) #we're counting the self signature


if __name__ == '__main__':
    unittest.main()