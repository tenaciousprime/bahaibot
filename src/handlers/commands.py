"""
    Copyright (c) 2018 Elliott Pardee <me [at] vypr [dot] xyz>
    This file is part of BibleBot.

    BibleBot is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    BibleBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with BibleBot.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys

import discord

from handlers.commandlogic import commandbridge as command_bridge

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + "/..")

import central  # noqa: E402

command_map = {
    "biblebot": 0,
    "search": 1,
    "versions": 0,
    "setversion": 1,
    "version": 0,
    "versioninfo": 1,
    "random": 0,
    "verseoftheday": 0,
    "votd": 0,
    "headings": 1,
    "versenumbers": 1,
    "languages": 0,
    "setlanguage": 1,
    "language": 0,
    "users": 0,
    "servers": 0,
    "invite": 0,

    "jepekula": 0,
    "joseph": 0,
    "tiger": 0,
    "supporters": 0,

    "addversion": 5
}


def is_command(command, lang):
    commands = lang["commands"]

    result = {
        "ok": False
    }

    if command == "setlanguage":
        result = {
            "ok": True,
            "orig": "setlanguage",
        }
    elif command == "ban":
        result = {
            "ok": True,
            "orig": "ban"
        }
    elif command == "unban":
        result = {
            "ok": True,
            "orig": "unban"
        }
    elif command == "eval":
        result = {
            "ok": True,
            "orig": "eval"
        }
    elif command == "jepekula":
        result = {
            "ok": True,
            "orig": "jepekula"
        }
    elif command == "joseph":
        result = {
            "ok": True,
            "orig": "joseph"
        }
    elif command == "tiger":
        result = {
            "ok": True,
            "orig": "tiger"
        }
    else:
        for original_command_name in commands.keys():
            if commands[original_command_name] == command:
                result = {
                    "ok": True,
                    "orig": original_command_name
                }

    return result


def is_owner_command(command, lang):
    commands = lang["commands"]

    if command == commands["leave"]:
        return True
    elif command == commands["puppet"]:
        return True
    elif command == commands["announce"]:
        return True
    elif command == commands["addversion"]:
        return True
    elif command == "ban":
        return True
    elif command == "unban":
        return True
    elif command == "eval":
        return True
    else:
        return False


class CommandHandler:
    @classmethod
    def process_command(cls, bot, command, lang, sender, args=None):
        raw_language = getattr("central.languages", lang).rawObject
        commands = raw_language["commands"]

        proper_command = is_command(command, raw_language)

        if proper_command["ok"]:
            orig_cmd = proper_command["orig"]
            if not is_owner_command(orig_cmd, raw_language):
                if orig_cmd != commands["search"]:
                    if orig_cmd != commands["headings"] and orig_cmd != commands["versenumbers"]:
                        if orig_cmd != commands["servers"] and orig_cmd != commands["users"]:
                            required_arguments = command_map[orig_cmd]

                            if args is None:
                                args = []

                            if len(args) != required_arguments:
                                embed = discord.Embed()

                                embed.color = 16723502
                                embed.set_footer(text=central.version,
                                                 icon_url=central.icon)

                                response = raw_language["argumentCountError"]
                                response = response.replace("<command>", command).replace(
                                    "<count>", str(required_arguments))

                                embed.add_field(name=raw_language["error"], value=response)

                                return {
                                    "isError": True,
                                    "return": embed
                                }

                            return command_bridge.run_command(orig_cmd, args, raw_language, sender)
                        else:
                            required_arguments = command_map[orig_cmd]

                            if args is None:
                                args = []

                            if len(args) != required_arguments:
                                embed = discord.Embed()

                                embed.color = 16723502
                                embed.set_footer(text=central.version, icon_url=central.icon)

                                response = raw_language["argumentCountError"]
                                response = response.replace("<command>", command).replace(
                                    "<count>", str(required_arguments))

                                embed.add_field(name=raw_language["error"], value=response)

                                return {
                                    "isError": True,
                                    "return": embed
                                }

                            return command_bridge.run_command(orig_cmd, [bot], raw_language, sender)
                    else:
                        if args is None:
                            args = []

                        if len(args) == 0 or len(args) == 1:
                            return command_bridge.run_command(orig_cmd, args, raw_language, sender)
                        else:
                            embed = discord.Embed()

                            embed.color = 16723502
                            embed.set_footer(text=central.version, icon_url=central.icon)

                            response = raw_language["argumentCountError"]
                            response = response.replace("<command>", command).replace(
                                "<count>", raw_language["zeroOrOne"])

                            embed.add_field(name=raw_language["error"], value=response)

                            return {
                                "isError": True,
                                "return": embed
                            }
                else:
                    if args is None:
                        args = []

                    if len(args) == 1 and len(args[0]) < 4:
                        embed = discord.Embed()

                        embed.color = 16723502
                        embed.set_footer(text=central.version, icon_url=central.icon)

                        embed.add_field(name=raw_language["error"], value=raw_language["queryTooShort"])

                        return {
                            "isError": True,
                            "return": embed
                        }

                    if len(args) == 0:
                        embed = discord.Embed()

                        embed.color = 16723502
                        embed.set_footer(text=central.version, icon_url=central.icon)

                        response = raw_language["argumentCountErrorAL"].replace(
                            "<command>", command).replace("<count>", "1")

                        embed.add_field(
                            name=raw_language["error"], value=response)

                        return {
                            "isError": True,
                            "return": embed
                        }
                    else:
                        return command_bridge.run_command(orig_cmd, args,
                                                          raw_language, sender)
            else:
                try:
                    if str(sender.id) == central.config["BibleBot"]["owner"] or str(sender.id) == "367665336239128577":
                        return command_bridge.run_owner_command(bot, command, args, raw_language)
                except Exception:
                    embed = discord.Embed()

                    embed.color = 16723502
                    embed.set_footer(text=central.version, icon_url=central.icon)

                    response = raw_language["commandNotFoundError"].replace(
                        "<command>", command)

                    embed.add_field(name=raw_language["error"], value=response)

                    return {
                        "isError": True,
                        "return": embed
                    }
        else:
            embed = discord.Embed()
            embed.color = 16723502
            embed.set_footer(text=central.version, icon_url=central.icon)

            response = raw_language["commandNotFoundError"].replace(
                "<command>", command)

            embed.add_field(name=raw_language["error"], value=response)

            return {
                "isError": True,
                "return": embed
            }
