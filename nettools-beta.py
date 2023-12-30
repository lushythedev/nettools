import discord
import requests
import os
import sys
import pytz
import socket
import subprocess
import platform
import json
from discord.ext import commands
from colorama import init, Fore, Back, Style
from datetime import datetime
from discord import Embed

# Colorama
init(autoreset=True)
RED = Fore.LIGHTRED_EX
GREEN = Fore.LIGHTGREEN_EX
YELLOW = Fore.LIGHTYELLOW_EX
CYAN = Fore.LIGHTCYAN_EX
RESET = Style.RESET_ALL

# Retrieve the token from environment variables
DISCORD_TOKEN = "#"
API_KEY = "#"

# Enable all standard intents and message content
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)


# Load the dictionary from the JSON file
with open('country_emojis.json', 'r') as file:
    country_emojis = json.load(file)

@bot.event
async def on_ready():
    print(f'{bot.user.name} {GREEN}has connected to Discord!')
    confirm = requests.get('http://ip-api.com/json/')
    if confirm.status_code == 200:
        print(f'{GREEN}API Connected (http://ip-api.com/){RESET}')
        print(f'{YELLOW}Awaiting commands...{RESET}')
    else:
        print(f'{RED}Not Connected!{RESET}')
        print(f'{RED}The server appears to be down. Please be patient and try again soon{RESET}')
        sys.exit()

@bot.event
async def on_command(ctx):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{GREEN}{ctx.author}{RESET} used {GREEN}{ctx.command}{RESET} at {GREEN}{current_time}{RESET}")

@bot.command(name='restart')
# Restricts this command to the bot's owner
async def restart(ctx):
    await ctx.send("Restarting bot...")
    await bot.close()
    sys.exit(1)  # Exit with status code 1

# Clock emoji mapping
clock_emojis = {
    0: "🕛", 1: "🕐", 2: "🕑", 3: "🕒", 4: "🕓",
    5: "🕔", 6: "🕕", 7: "🕖", 8: "🕗", 9: "🕘",
    10: "🕙", 11: "🕚", 12: "🕛", 13: "🕐", 14: "🕑",
    15: "🕒", 16: "🕓", 17: "🕔", 18: "🕕", 19: "🕖",
    20: "🕗", 21: "🕘", 22: "🕙", 23: "🕚"
}

def get_geolocation(query):
    base_url = "http://ip-api.com/json/"
    url = base_url + query
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@bot.command(name='lookup')
async def lookup(ctx, *, query: str):
    geolocation_info = get_geolocation(query)

    if geolocation_info and geolocation_info.get('status') == 'success':
        # Fetch the country code
        country_code = geolocation_info.get('countryCode', '').lower()
        country_flag_emoji = f":flag_{country_code}:" if country_code else ""
        city_emoji = ":cityscape:"
        server_info = "<:server_location:1190423704434384916>"
        world_emoji = '<:world_info:1190426132613435462>'


        # Determine the local time for the IP's timezone
        timezone = geolocation_info.get('timezone', 'UTC')
        local_time = datetime.now(pytz.timezone(timezone))
        hour = local_time.hour
        clock_emoji = clock_emojis.get(hour, "🕛")

        # Create the embed message
        embed = discord.Embed(title="IP Address Information:", color=2752442)
        embed.description = (
            f"Country: {geolocation_info.get('country', 'N/A')} {country_flag_emoji}\n"
            f"Country Code: {country_code.upper()}\n"
            f"Region: {geolocation_info.get('regionName', 'N/A')}\n"
            f"City: {geolocation_info.get('city', 'N/A')} {city_emoji}\n"
            f"Zip: {geolocation_info.get('zip', 'N/A')}\n"
            f"Lat: {geolocation_info.get('lat', 'N/A')}\n"
            f"Lon: {geolocation_info.get('lon', 'N/A')}\n"
            f"Timezone: {timezone}\n"
            f"Local Time: {local_time.strftime('%Y-%m-%d %H:%M:%S')} {clock_emoji}\n"
            f"ISP: {geolocation_info.get('isp', 'N/A')}\n"
            f"ORG: {geolocation_info.get('org', 'N/A')} {world_emoji}\n"
            f"AS: {geolocation_info.get('as', 'N/A')}\n"
            f"IP Query: {query} {server_info}"
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("Error: Unable to retrieve data or invalid IP/Query.")
        ping()

@bot.command(name='ping')
async def ping(ctx, ip: str):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    try:
        response = subprocess.run(['ping', param, '1', ip], capture_output=True, text=True, timeout=5)
        embed_color = 2752442  # Custom color

        if response.returncode == 0:
            # Parse response to extract data
            # This parsing depends on your ping command's output format
            # You may need to adjust it according to your actual ping output
            bytes_data, icmp_seq, ttl, time_ms, packets_transmitted, packets_received, packet_loss, min_ms, avg_ms, max_ms, stddev_ms = parse_ping_output(response.stdout)

            embed_description = (
                f"`Status`: Success ✅\n"
                f"`Response Results:` ⏎\n"
                f"`Sent:` {bytes_data} bytes of data to {ip}\n"
                f"`Received:` {bytes_data} bytes of data back from {ip}\n "
                f"`Info:` icmp_seq={icmp_seq} ttl={ttl} time={time_ms} ms\n\n"
                f"`---` {ip} ping statistics `---`\n"
                f"`{packets_transmitted}` packets transmitted, `{packets_received}` packets received, `{packet_loss}%` packet loss\n\n"
                # f"round-trip **min**/**avg**/**max**/**stddev** = `{min_ms}`/`{avg_ms}`/`{max_ms}`/`{stddev_ms}`"
            )
        else:
            embed_description = f"Failed to ping {ip}."

        embed = discord.Embed(title=f"Ping Results for {ip}", description=embed_description, color=embed_color)
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="Error", description=str(e), color=0xff0000)
        await ctx.send(embed=embed)

def parse_ping_output(output):
    lines = output.split('\n')
    # Example parsing logic (this will vary based on your ping output format)
    data_sent_info = lines[0]
    data_received_info = lines[1]
    stats_info = lines[-1]

    # Extracting data - this is highly dependent on your specific ping output format
    bytes_of_data = "32"  # Example, extract actual value from data_sent_info
    icmp_seq = "1"  # Example, extract actual value
    ttl = "128"  # Example, extract actual value
    time_ms = "100"  # Example, extract actual value
    packets_transmitted = "4"  # Example, extract actual value from stats_info
    packets_received = "4"  # Example, extract actual value from stats_info
    packet_loss = "0%"  # Example, extract actual value from stats_info
    round_trip_times = "1/2/3/4"  # Example, extract actual value from stats_info

    return (bytes_of_data, icmp_seq, ttl, time_ms, packets_transmitted, packets_received, packet_loss, *round_trip_times.split('/'))


@bot.command(name='checkport')
async def check_port(ctx, ip: str, port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Timeout of 1 second for the check
    result = sock.connect_ex((ip, port))
    if result == 0:
        await ctx.send(f"Port {port} is open on {ip}.")
    else:
        await ctx.send(f"Port {port} is closed on {ip}.")
    sock.close()

@bot.command(name='reverse')
async def reverse(ctx, domain: str):
    try:
        ip_address = socket.gethostbyname(domain)
        embed = discord.Embed(title="Domain IP Lookup", description=f"The IP address of `{domain}` is `{ip_address}`.", color=2752442)
    except Exception as e:
        embed = discord.Embed(title="Error", description=str(e), color=2752442)

    await ctx.send(embed=embed)

@bot.command(name='commands')
async def commands(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of available network-related commands", color=2752442)
    embed = discord.Embed(title="Bot Commands", description="List of available network-related commands", color=2752442)
    embed.add_field(name="`!ping [IP]`", value="Checks the latency to the given IP address.", inline=False)
    embed.add_field(name="`!reverse [domain]`", value="Finds the IP address for the given domain.", inline=False)
    embed.add_field(name="`!lookup [IP/domain]`", value="Provides geolocation information for the given IP or domain.", inline=False)
    embed.add_field(name="`!reversewhois [IP]`", value="Performs a reverse WHOIS lookup for the given IP address.", inline=False)
    embed.add_field(name="`!nslookup [domain]`", value="Performs a DNS lookup for the specified domain.", inline=False)
    embed.add_field(name="`!restart`", value="Restarts the bot. (Owner only)", inline=False)
    embed.add_field(name="`!whois [domain/IP]`", value="Retrieves WHOIS information for a given domain or IP address.", inline=False)
    embed.add_field(name=":x: `[DISABLED]` !dnslookup [domain]", value="Performs a DNS lookup for the specified domain.", inline=False)
    embed.add_field(name=":x: `[DISABLED]` !portscan [IP]", value="Scans commonly used ports of a given IP address.", inline=False)
    embed.add_field(name=":x: `[DISABLED]` !trace [IP/domain]", value="Conducts a traceroute to a specified IP or domain.", inline=False)
    embed.add_field(name=":x: `[DISABLED]` !subnetcalc [IP/subnet mask]", value="Calculates the subnet information for a given IP and subnet mask.", inline=False)
    # Add more commands here as your bot expands
    await ctx.send(embed=embed)

# Format JSON For Embed

def format_whois_data(data):
    formatted_data = []
    for key, value in data.items():
        if isinstance(value, list):  # If the value is a list
            # Handle lists of dictionaries (e.g., 'owner', 'admin', 'tech')
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    formatted_data.append(f"{key.capitalize()} {i+1}:")
                    for subkey, subvalue in item.items():
                        formatted_data.append(f"  - {subkey.capitalize()}: {subvalue or 'N/A'}")
        elif isinstance(value, dict):  # If the value is a dictionary
            formatted_data.append(f"{key.capitalize()}:")
            for subkey, subvalue in value.items():
                formatted_data.append(f"  - {subkey.capitalize()}: {subvalue or 'N/A'}")
        else:
            formatted_data.append(f"{key.capitalize()}: {value or 'N/A'}")
    return "\n".join(formatted_data)

# Make Embed Prettier

def pretty_json(data):
    data.pop('rawdata', None)  # Remove rawdata if exists
    return json.dumps(data, indent=2)

@bot.command(name='whois')
async def whois(ctx, domain: str):
    url = f"https://whoisjson.com/api/v1/whois"
    headers = {
        'accept': 'application/json',
        'Authorization': f'TOKEN={API_KEY}'
    }
    params = {'domain': domain, 'format': 'json'}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            # Prepare the JSON data for the embed description
            formatted_json = pretty_json(data)
            embed_description = f"```json\n{formatted_json}\n```"

            # Ensure the formatted JSON does not exceed Discord's embed limits
            if len(embed_description) > 2048:
                embed_description = embed_description[:2045] + "\n...```"  # Truncate and close the code block

            embed = Embed(title=f"Whois Report for {domain}", description=embed_description, color=5814783)
            
        else:
            embed = Embed(title="Error", description=f"Failed to retrieve WHOIS data. Status: {response.status_code}", color=0xe74c3c)

        await ctx.send(embed=embed)
    except Exception as e:
        embed = Embed(title="Error", description=str(e), color=0xe74c3c)
        await ctx.send(embed=embed)

@bot.command(name='reversewhois')
async def reversewhois(ctx, ip: str):
    url = "https://whoisjson.com/api/v1/reverseWhois"
    headers = {'accept': 'application/json', 'Authorization': f'TOKEN={API_KEY}'}
    params = {'ip': ip}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            # Correctly using pop to remove 'rawdata'
            if 'rawdata' in data:
                data.pop('rawdata')  # Removes 'rawdata' if it exists
            pretty_data = json.dumps(data, indent=2)
            await ctx.send(f"```json\n{pretty_data}\n```")
        else:
            await ctx.send(f"Error: {response.status_code}")
    except Exception as e:
        await ctx.send(str(e))

@bot.command(name='nslookup')
async def nslookup(ctx, domain: str):
    url = "https://whoisjson.com/api/v1/nslookup"
    headers = {'accept': 'application/json', 'Authorization': f'TOKEN={API_KEY}'}
    params = {'domain': domain}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            pretty_data = json.dumps(data, indent=2)
            await ctx.send(f"```json\n{pretty_data}\n```")
        else:
            await ctx.send(f"Error: {response.status_code}")
    except Exception as e:
        await ctx.send(str(e))

bot.run(DISCORD_TOKEN)