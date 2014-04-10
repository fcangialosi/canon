"""

Author: Frank Cangialosi, 2014
fcangial@umd.edu

Source available at: https://github.com/sbfcangialosi/canon

Canon automates the process of downloading, running, and 
diffing student tests against the canonicals posted on Piazza 
for Meeshquest

Please see the README for general use instructions
python canon.py --help for info on specific command-line options

"""
import urllib2
from cookielib import CookieJar
from pprint import pprint
import json
import HTMLParser
import re
import subprocess
import sys
import os.path
from os.path import join, dirname, isfile
import argparse
from pprint import pprint

parser = argparse.ArgumentParser(prog='Canon', description="Canon automates the process of downloading, running, and diffing student tests against the canonicals posted on Piazza for Meeshquest")
parser.add_argument('-e', '--email', help="E-mail address of your Piazza account, required for authentication.", required=True)
parser.add_argument('-p', '--password', help="Password of your Piazza account, required for authentication.", required=True)
parser.add_argument('-j', '--jar', help="Path to executable JAR of your code. Please see README for instructions on how to create an appropriate JAR file.", required=True)
parser.add_argument('-v', '--verbose', help="Use this flag to see the results of all diffs against the canonical", action="store_true")
parser.add_argument('--NO-DOWNLOAD', help="Use this flag to skip the downloading step and use any XML files currently in './inputs'", action="store_true")
args = vars(parser.parse_args())

# Used for printin success/fail results with ASCII colors
green_start = '\033[0;32m'
red_start = '\033[0;31m'
color_end = '\033[00m'

def print_s(string):
	print green_start + string + color_end

def print_e(string):
	print red_start + string + color_end

# Make sure the JAR file is there before we go through the trouble of downloading everything
if(not os.path.exists(args['jar'])):
	print_e("Cannot find the JAR file '{0}', please check the path.".format(args['jar']))
	sys.exit(0)

# First post ID to check
cid = 122
base_url = "https://piazza.com/class/hq5glzx49lp56f?cid="
url_regex = re.compile("(https://\S[^\"]+)")

# Check if necessary folders exist, and if not, create them
files_exist = True
current_dir = os.path.dirname(os.path.realpath(__file__))
print "Necessary directories? ", 
sys.stdout.flush()
dirs = [(current_dir+"/"+x) for x in ["inputs","my_outputs","canonical_outputs"]]
for folder in dirs:
	if(not os.path.exists(folder)):
		files_exist = False
		os.makedirs(folder)
if(not files_exist):
	print_s("Created.")
else:
	print_s("Already exist.")

# Initialize cookie tracker and request opener
cj = CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

login_url = 'https://piazza.com/logic/api?method=user.login'
login_data = '{"method":"user.login","params":{"email":"fcangial@terpmail.umd.edu","pass":"frankfrank94"}}'
#login_data = '{"method":"user.login","params":{"email":"{0}","pass":"{1}"}}'.format(args['email'],args['password'])
# Authenticate
login_resp = opener.open(login_url, login_data)
if(not login_resp):
	print_e("No response from server. Piazza may be down, or you may have lost internet connection.")
	sys.exit(0)
result = json.loads(login_resp.read())
if(not result['result'] == 'OK'):
	print_e("Authentication failed. Make sure the e-mail and password you provided correspond to a Piazza account!")
	sys.exit(0)

posts = [] # array of quadruples of the form (post_url, [input_urls], [output_urls])

print "Searching Piazza..",
sys.stdout.flush()
# Find posts with student tests, and collect links
while cid < 200:
	# Get piazza post for CMSC420 Spring 2014 with CID cid
	content_url = 'https://piazza.com/logic/api?method=get.content'
	content_data = '{"method":"content.get","params":{"cid":"'+str(cid)+'","nid":"hq5glzx49lp56f"}}'
	content_resp = opener.open(content_url,content_data)
	cid += 1
	if(not content_resp):
		print_e("No response from server. Piazza may be down, or you may have lost internet connection.")
		sys.exit(0)
	result = json.loads(content_resp.read())
	if(not result['result']):
		continue
	else:			
		html = result['result']['history'][0]['content'] # Main post HTML
		if("<a href" in html): # Post contains a link, most likely to an XML file
			inputs = url_regex.findall(html)
			if(not inputs): # The link wasn't an XML input after all, keep going
				continue
			inputs = [x.replace("\\","") for x in inputs]
			if(result['result']['children']):
				html = result['result']['children'][0]['history'][0]['content']
				if("<a href" in html): # Instructor has responded
					outputs = url_regex.findall(html)
					# Even if there aren't any outputs, still want to DL input, we'll handle empty outputs [] later
					outputs = [x.replace("\\","") for x in outputs]
				posts.append({'post_url' : base_url + str(cid-1), 'input_urls' : inputs, 'output_urls' : outputs}) 

print_s("Found " + str(len(posts)) + " posts with test cases. " + color_end)

xml_regex = re.compile("https://\S*\/(.*)\.xml")
file_regex = re.compile("https://\S*\/(.*\.\S+)")
zip_regex = re.compile("inflating: (\S+)")
i_count = 0
o_count = 0
bad_posts = []

for post in posts:
	for i in range(len(post['input_urls'])):
		url = post['input_urls'][i]
		input_resp = urllib2.urlopen(url)
		if(not input_resp):
			print_e("No response from cloudfront server. The URL ({0}) may be malformed, or your connection may be down.".format(url))
			sys.exit(0)
		input_xml = input_resp.read()
		if(not "xml" in url):
			continue
		if('output' in url):
			bad_posts.append(post)
			break
		base = xml_regex.findall(url)[0]
		if(not "input" in base):
			base += '.input.xml'
		elif(not "xml" in base):
			base += '.xml'
		f = open(dirs[0] + "/" + base, 'w')
		f.write(input_xml)
		f.close()
		if(not 'input_names' in post):
			post['input_names'] = [base]
		else:
			post['input_names'].append(base)
		i_count += 1
	if(not 'output' in url):
		for i in range(len(post['output_urls'])):
			url = post['output_urls'][i]
			output_resp = urllib2.urlopen(url)
			if(not output_resp):
				print_e("No response from cloudfront server. The URL ({0}) may be malformed, or your connection may be down.".format(url))
				sys.exit(0)
			output_file = output_resp.read()
			name = file_regex.findall(url)[0]
			f = open(dirs[2] + "/" + name, 'w')
			f.write(output_file)
			f.close()
			if(not 'output_names' in post):
				post['output_names'] = [name]
			else:
				post['output_names'].append(name)
			if('xml' in name):
				o_count += 1
			if('zip' in name):
				cmd = ['unzip', dirs[2] + "/" + name, '-d', dirs[2]]
				p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
				out, err = p.communicate()
				unzipped = zip_regex.findall(out)
				for f in unzipped:
					post['output_names'].append(f)
					if('xml' in f):
						o_count += 1
for post in bad_posts:
	posts.remove(post)

print_s("Successfully downloaded {0} input and {1} output files".format(i_count,o_count))

correct = 0
total = 0
results_text = ""
print "Running all tests, and storing outputs in " + dirs[1]
for post in posts:
	total += 1
	ins = [x for x in post['input_names'] if 'xml' in x]
	outs = [x for x in post['output_names'] if 'xml' in x]
	if('mapstuff' in ins[0]):
		temp = ins[0]
		ins[0] = ins[1]
		ins[1] = temp

	for i in range(len(ins)):
		in_name = dirs[0] + "/" + ins[i]
		in_f = open(in_name)
		if dirs[2] in outs[i]:
			out_name = outs[i]
		else:
			out_name = dirs[1] + "/" + outs[i]
		out_f = open(out_name,'w')
		cmd = ['java', '-jar', args['jar']]
		p = subprocess.call(cmd,stdin=in_f,stdout=out_f)
		# out, err = p.communicate()
		# if(err):
		# 	print("["+red_start + u'\u2717' + color_end+" ]: " + ins[i] + "..." + red_start +"threw an exception." + color_end)
		in_f.close()
		out_f.close()
		
		cmd = ['diff', out_name, dirs[2] + "/" + outs[i]]
		p = subprocess.Popen(cmd,stdout=subprocess.PIPE)
		out, err = p.communicate()
		if(not out.strip()):
			 print("["+green_start + u'\u2713' + color_end+" ]: " + ins[i])
			 correct+=1
		else:
			print("["+red_start + u'\u2717' + color_end+" ]: " + ins[i] + "..." + red_start + "outputs did not match." + color_end)
		results_text += out
		results_text += "\n"

f = open('results.txt','w')
f.write(results_text)
f.close()

print "({0}/{1}) student tests passed.".format(correct, total)