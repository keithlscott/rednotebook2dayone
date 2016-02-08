#!/usr/bin/python

import os
import re
import datetime
import pytz
import pexpect

INPUTDIR="/Users/kscott/Desktop/CalConvert/rednotebook"
OUTPUTDIR="/Users/kscott/Desktop/CalConvert/dayone"

def processEntry(e):
    # These are the regular expressions that we use to munge rednotebook
    # entries into DayOne entries.
    things = (('^=([^=\r]*)=\r',       '# \\1\r'), # Replace level-1 headers
              ('\r=([^=\r]*)=\r',       '# \\1\r'), # Replace level-1 headers
              ('\r==([^=\r]*)==\r',     '## \\1\r'), # Replace level-2 headers
              ('\r===([^=\r]*)==\r',    '### \\1\r'), # Replace level-3 headers
              ('\r====([^=\r]*)==\r',   '#### \\1\r'), # Replace level-4 headers
              ('\r=====([^=\r]*)==\r',  '##### \\1\r'), # Replace level-5 headers
              ('\r======([^=\r]*)==\r', '###### \\1\r'), # Replace level-6 headers
              ('&', '&amp;'), # DayOne doesn't like naked '&'
              ('<', '&lt;'), # DayOne doesn't like naked '<'
              ('>', '&gt;'), # DayOne doesn't like naked '<'
              ('//([^\r]*)//', '*\\1*') # Italic conversion
              )

    e = e.strip()
    parts = e.split(':')
    if len(parts)==1:
        return
    
    # Figure out tags
    bot = e.find('{')+1
    endOfTags = e.find('text:')
    
    theTags = []
    if ( bot==endOfTags ):
        pass
    else:
        tagsPart = e[bot:endOfTags]
        toks = tagsPart.split(',')
        for t in toks:
            colon = t.find(':')
            if len(t[0:colon].strip())>0:
                theTags += [t[0:colon].strip()]
    
    # Process the text of the entry.
    start = e.find('text: ') + len('text: ') + 1
    foo = e[start:len(e)-1]
    foo1 = foo.replace('\n    ', ' ')
    foo2 = foo1.replace('\\n', '\r')
    foo3 = foo2.replace('\\t', '\t')
    # OK, now foo3 is the basic converted text.  Need to deal with difference
    # in markup.
    
    tmp = foo3
    for t in things:
        tmp = re.sub(t[0], t[1], tmp)
    
    # parts[0] is the day of the month identified by the filename
    # tmp is the new text
    return((parts[0], tmp, theTags))
    
def processFile(f):
    fName = os.path.basename(f.name).split('.')
    yearMonth = fName[0].split('-')
    
    entriesDone = []
    data = f.read()
    data = data.split('}\n')
    print "File %s has %d entries." % (f.name, len(data))
    for e in data:
        if len(e)<10:
            continue
        (dayOfMonth, text, tags) = processEntry(e)
        
        ret = makeDayOneEntry(yearMonth + [dayOfMonth], text, tags)
        entriesDone += [yearMonth+[dayOfMonth]]
        print ret
        
    print "Done with all entries"
    for e in entriesDone:
        print e
    f.close()
    
def doDirectory():
    
    for theFile in os.listdir(INPUTDIR):
        if theFile[0] == '.':
            continue
        
        print "File is: " + theFile
        f = open(INPUTDIR+"/"+theFile, 'r')
        processFile(f)
        f.close()
        print "done"

def makeDayOneEntry(yearMonthDay, text, tags):
    part1 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Creation Date</key>
        <date>'''
    # Date in the form: 	<date>2016-02-07T13:42:46Z</date>
    print "yearMonthDay is: ", yearMonthDay
    print yearMonthDay[0], yearMonthDay[1], yearMonthDay[2]
    theDate = datetime.datetime(int(yearMonthDay[0]), int(yearMonthDay[1]), int(yearMonthDay[2]),
                                8,0,0)
    fmt = '%Y-%m-%dT%H:%M:%SZ'
    
    uuid = pexpect.run('/bin/bash -c "uuidgen | sed s/-//g"').strip()
    
    part2 = '''</date>
	<key>Creator</key>
	<dict>
		<key>Device Agent</key>
		<string>Macintosh/iMac12,2</string>
		<key>Generation Date</key>
                <date>'''
    # Date in the form: 	<date>2016-02-07T13:42:46Z</date>
   
    part3 = '''</date>
		<key>Host Name</key>
		<string>Keith Scott’s iMac</string>
		<key>OS Agent</key>
		<string>MacOS/10.11.3</string>
		<key>Software Agent</key>
		<string>Day One Mac/1.10.2</string>
	</dict>
	<key>Entry Text</key>
        <string>'''
   # Entry text in Markdown here
   
    part4 = '''</string>
	<key>Starred</key>
	<false/>
	<key>Tags</key>'''
    # Tags in the form: <string>Test_Tag1</string>
    
    # if no tags then just <array/>
    
    part5 = '''
	<key>Time Zone</key>
	<string>America/New_York</string>
	<key>UUID</key>
	<string>'''
    # UUID in the form: D3779595C4DE47A4BA50F2959A15392D
    
    part6 = '''</string>
</dict>
</plist>
'''
    ret = ""
    
    ret += part1
    ret += theDate.strftime(fmt)
    ret += part2
    ret += theDate.strftime(fmt)
    ret += part3
    ret += text
    ret += part4
    ret += '\r\t<array>\r'
    for t in tags:
        ret += '\t\t<string>'
        ret += t
        ret += '</string>\r'
    ret += '\t</array>\r'
    ret += part5
    ret += uuid
    ret += part6
    
    f = open(OUTPUTDIR+'/'+uuid+'.doentry', 'w')
    f.write(ret)
    f.close()
    return ret

if __name__=='__main__':
    doDirectory()
