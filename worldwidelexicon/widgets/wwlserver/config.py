# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Configuration Module (config.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements classes that contain root system settings, global constants,
prompt settings and localization profiles. This information would normally be stored
in conventional configuration files, but because of the way App Engine functions, it
is easier and more efficient to write a Python class as a container for these items.

Copyright (c) 1998-2009, Worldwide Lexicon Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer. Web services
      derived from this software must provide a link to www.worldwidelexicon.org
      with a "translations powered by the Worldwide Lexicon" caption (or
      appropriate translation.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of the Worldwide Lexicon Inc/Worldwide Lexicon Project
      nor the names of its contributors may be used to endorse or promote
      products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# Python modules
import string

class Config():
    """
    This class contains global/root system settings
    """
    # main system prompts and language settings
    # default source language for system, prompts, etc
    sl = 'en'
    # title to display in header and masthead on home pages
    title = 'Der Mundo'
    # subtitle to display in header and masthead on home pages
    subtitle = 'The World In Your Language'
    # root username
    rootuser = ''
    # root pw
    rootpw = ''
    #
    # subscribe to receive updates from other WWL translation
    # memories. when enabled, your server will contact other
    # WWL servers to request updates as users submit translations
    # and scores. this mirroring service allows all WWL servers to
    # function as a global translation memory. you can create your
    # own private network of WWL mirrors, or can slave them to the
    # public WWL translation memory (default setting)
    #
    subscribe_to = ['www.worldwidelexicon.org']
    share_to_wwl = True
    # contact bsmcconnell@gmail.com to register your WWL node with
    # the public translation memory
    share_to_username = None
    share_to_pw = None
    #
    # external web services, API keys, etc
    #
    # Machine Translation APIS
    mt_default = 'google'
    worldlingo_api = 'S000.1'
    worldlingo_pw = 'secret'
    # define World Lingo language pairs here
    # ...
    #
    # Professional Language Service Providers
    speaklike_languages = ['ar','bg','ca','zh','zt','hr','cs','da','nl','en','fr','de','el','iw','ht','hi','hu','it','ja','ko','no','fa','pl','pt','ro','ru','es','sr','th','tr','uk','ur']
    @staticmethod
    def lspurl(lspname):
        if lspname == 'proz':
            return 'http://www.proz.com/workorder/api'
        else:
            return ''
