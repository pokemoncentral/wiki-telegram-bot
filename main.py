#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 02:28:47 2017

@title: PCW_bot
@author: SimplyAero
"""


import re
import sys
import json
import urllib.request

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    ParseMode
)
from telegram.ext import Updater, InlineQueryHandler


PCW = "https://wiki.pokemoncentral.it/api.php?"
TOKEN = sys.argv[-1]
HTML_REGEX = re.compile(r"<[\w/ =\"]+>", re.IGNORECASE)


class PageNotFoundError(Exception):
    pass


class Page:
    """
    @name: Page
    @description: Class representing a wiki page
    """

    opensearch = "action=opensearch&"\
                 "format=json&"\
                 "search={0}&"\
                 "namespace=0&"\
                 "limit=10&"\
                 "redirects=resolve&"\
                 "utf8=1&formatversion=2"

    extract_query = "action=query&"\
                    "format=json&"\
                    "prop=extracts&"\
                    "indexpageids=1&"\
                    "titles={0}&"\
                    "utf8=1&"\
                    "formatversion=2&"\
                    "exchars=71&"\
                    "exsectionformat=raw"

    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url
        query = Page.extract_query.format(title)
        result_bytes = urllib.request.urlopen(PCW + query).read()
        result_json = result_bytes.decode("utf-8")
        result = json.loads(result_json)
        extract = result["query"]["pages"][0]["extract"]
        extract = HTML_REGEX.sub("", extract)
        extract = extract.replace("  ", " ")
        self.url = self.url.replace("(", "%28")
        self.url = self.url.replace(")", "%29")
        self.extract = extract

    def __str__(self):
        to_return = "*{0}*\n" + self.extract + " [(Continua a leggere)]({1})"
        return to_return.format(self.title, self.url)


def get_pages(to_search: str) -> list:
    query = Page.opensearch.format(to_search)
    result_bytes = urllib.request.urlopen(PCW + query).read()
    result_json = result_bytes.decode("utf-8")
    result = json.loads(result_json)
    if len(result[1]) < 1:
        raise PageNotFoundError
    else:
        titles = result[1]
        urls = result[3]
        pages = []
        for index in range(len(titles)):
            pages.append(Page(titles[index], urls[index]))
    return pages


def inline_pages(bot, update):
    query = update.inline_query.query
    if query:
        results = list()
        try:
            pages = get_pages(query)
            for page in pages:
                content = str(page)
                new_result = InlineQueryResultArticle(
                    id=page.title,
                    title=page.title,
                    input_message_content=InputTextMessageContent(
                        content,
                        parse_mode=ParseMode.MARKDOWN
                    )
                )
                results.append(new_result)
        except PageNotFoundError:
            new_result = InlineQueryResultArticle(
                id="Pagina non trovata",
                title="Pagina non trovata",
                input_message_content=InputTextMessageContent(query)
            )
            results = [new_result]
        bot.answer_inline_query(update.inline_query.id, results)


def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    inline_page_finder = InlineQueryHandler(inline_pages)
    dispatcher.add_handler(inline_page_finder)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
