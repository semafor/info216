#!/usr/bin/python3

import re
import string
import json

# file = 'Spacelog/missions/a13/transcripts/TEC'
file = 'bridged/a13-problem'

# Defaults to STDOUT
out = None

PREFIX = 'http://apollo.nasa.gov/KB'

NASA = 'http://dbpedia.org/page/NASA'
SPACELOG = 'https://github.com/Spacelog/Spacelog/'

LOVELL = PREFIX + '#jamesarthurlovelljr'
HAISE = PREFIX + '#fredwallacehaisejr'
HOUSTON = PREFIX + '#mcc'
SWIGERT = PREFIX + '#johnleonardswigertjr'
LOUSMA = PREFIX + '#jackrobertlousmausmc'
APOLLO13 = PREFIX + '#apollo13'

LIFTER = PREFIX + '#ApolloLifterProgram'


KB_TO_NASA = {}
KB_TO_NASA[LOVELL] = "http://data.kasabi.com/dataset/nasa/person/jamesarthurlovelljr"  # nopep8
KB_TO_NASA[HAISE] = "http://data.kasabi.com/dataset/nasa/person/fredwallacehaisejr"  # nopep8
KB_TO_NASA[HOUSTON] = "https://www.wikidata.org/wiki/Q5112041"  # nopep8
KB_TO_NASA[SWIGERT] = "http://data.kasabi.com/dataset/nasa/person/johnleonardswigertjr"  # nopep8
KB_TO_NASA[LOUSMA] = "http://data.kasabi.com/dataset/nasa/person/jackrobertlousma"  # nopep8
KB_TO_NASA[APOLLO13] = "http://data.kasabi.com/dataset/nasa/mission/apollo-13"  # nopep8

with open('Spacelog/missions/shared/glossary/apollo') as data_file:
    glossary = json.load(data_file)


def print_resource_triple(s, p, o):
    print('<%s> <%s> <%s>' % (s, p, o))


def print_literal_triple(s, p, o):
    print('<%s> <%s> %s' % (s, p, o))

def print_raw_triple(s, p, o):
    print('%s %s %s' % (s, p, o))


def print_turtle_predicate_triple(s, p, o):
    print('<%s> %s <%s>' % (s, p, o))


def print_turtle_triple(s, p, o):
    print('<%s> %s %s' % (s, p, o))


def get_timestamp_match(text):
    r = re.compile('\[(?P<day>\d+)\:(?P<hour>\d+)\:(?P<minute>\d+)\:(?P<second>\d+)\]')  # nopep8
    return r.match(text)


def get_meta_match(text):
    r = re.compile('^_')
    return r.match(text)


def get_speaker(text):
    r = re.compile('^(?P<speaker>\w+)\:\ .+')
    rm = r.match(text)
    if rm:
        return rm.group('speaker')
    else:
        return None


def get_spoken(text):
    r = re.compile('^\w+\:\ (?P<spoken>.+)')
    rm = r.match(text)
    if rm:
        return rm.group('spoken')
    else:
        return None


def get_glossary(text):
    r = re.compile('.+\[glossary\:(?P<term>.+)\].+')
    rm = r.match(text)
    if rm:
        return rm.group('term')
    else:
        return None


def timestamp_to_abs_seconds(ts_match):
    day = ts_match.group('day')
    hour = ts_match.group('hour')
    minute = ts_match.group('minute')
    second = ts_match.group('second')

    day_secs = int(day) * 86400
    hour_secs = int(hour) * 3600
    minute_secs = int(minute) * 60

    return day_secs + hour_secs + minute_secs + int(second)


def timestamp_to_human_readable(ts_match):
    day = int(ts_match.group('day'))
    hour = int(ts_match.group('hour'))
    minute = int(ts_match.group('minute'))
    second = int(ts_match.group('second'))

    return '%02d:%02d:%02d:%02d' % (day, hour, minute, second)


def timestamp_to_abs_hours_timestamp(ts_match):
    day = ts_match.group('day')
    hour = ts_match.group('hour')
    minute = ts_match.group('minute')
    second = ts_match.group('second')

    day_hours = int(day) * 24
    # hour_hours = int(hour) * 3600
    # minute_hours = int(minute)
    total_hours = day_hours + int(hour)
    return '%02d_%02d_%02d' % (total_hours, int(minute), int(second))


def set_speaker(event):
    speaker = get_speaker(event['text'])
    if speaker:
        event['speaker'] = {
            'CDR': LOVELL,
            'LMP': HAISE,
            'CC': HOUSTON,
            'CMP': SWIGERT,
            'SC': '#unidentified'
        }[speaker]


def set_spoken(event):
    spoken = get_spoken(event['text'])
    if spoken:
        event['spoken'] = spoken


def set_glossary(event):
    term = get_glossary(event['text'])

    if term:
        if 'terms' not in event:
            event['terms'] = []
        event['terms'].append(term)


def dereference_identifier(speaker, ref):
    # Apollo 13 speaking
    unambiguous = {
        'fred': HAISE,
        'fred-o': HAISE,
        '13': APOLLO13,
    }
    if speaker == LOVELL or speaker == SWIGERT or speaker == HAISE:
        lookup = {
            'jack': LOUSMA,
            'us': APOLLO13,
            'we': APOLLO13,
            'me': speaker,
            'i': speaker,
            'our': APOLLO13,
            'ourselves': APOLLO13,
            'you': HOUSTON,
            'your': HOUSTON,
            'youre': HOUSTON,
            'yourselves': HOUSTON,
            'they': HOUSTON,
            'theyre': HOUSTON,
            'houston': HOUSTON,
            'wed': HOUSTON,
        }
        lookup.update(unambiguous)
        return lookup.get(ref, None)
    elif speaker == HOUSTON:
        lookup = {
            'jack': SWIGERT,
            'us': HOUSTON,
            'we': HOUSTON,
            'i': speaker,
            'our': HOUSTON,
            'ourselves': HOUSTON,
            'you': APOLLO13,
            'your': APOLLO13,
            'youre': APOLLO13,
            'yourselves': APOLLO13,
            'they': APOLLO13,
            'theyre': APOLLO13,
            'cmc': HOUSTON,
            'houston': HOUSTON,
            'wed': HOUSTON,
        }
        lookup.update(unambiguous)
        return lookup.get(ref, None)


def set_participants(event):
    words = event['spoken'].split(' ')
    event['participants'] = set()
    speaker = event['speaker']

    for word in words:
        word = word.lower()

        # remove punctuation
        exclude = set(string.punctuation)
        word = ''.join(ch for ch in word if ch not in exclude)
        deref = dereference_identifier(speaker, word)
        if deref:
            event['participants'].add(deref)
        # else:
        #     print(word)


tec = open(file)

# seconds to a string
events = {}
cur_event = None

for line in tec:
    ts = get_timestamp_match(line)
    if ts:
        abs_secs = timestamp_to_abs_seconds(ts)
        cur_event = abs_secs
        events[cur_event] = {'text': ''}

        if 'mission_timer' not in events[cur_event]:
            events[cur_event]['mission_timer'] = 'GET_' + timestamp_to_abs_hours_timestamp(ts)  # nopep8
            events[cur_event]['readable_mission_time'] = timestamp_to_human_readable(ts)  # nopep8
    else:
        if not get_meta_match(line):
            l = line.replace('\n', '').strip()
            events[cur_event]['text'] += l + ' '


for secs, event in events.items():
    set_speaker(event)
    set_spoken(event)
    set_participants(event)
    set_glossary(event)


# print(events)

print("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>")
print("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>")
print("PREFIX owl: <http://www.w3.org/2002/07/owl#>")
print("PREFIX prov: <http://www.w3.org/ns/prov#>")
print("PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>")

for actor in [LOVELL, HAISE, HOUSTON, SWIGERT, LOUSMA]:
    print("""
<%s> a sem:Actor, prov:Person ;
     owl:sameAs <%s> ;
     prov:actedOnBehalfOf <%s> .""" % (actor, KB_TO_NASA[actor], NASA))

print("""
<%s> a sem:Object, sem:Place, prov:Location ;
     owl:sameAs <%s> .""" % (APOLLO13, KB_TO_NASA[APOLLO13]))

print("""
<%s> a sem:Object, sem:Place, prov:Location ;
     owl:sameAs <%s> .""" % (HOUSTON, KB_TO_NASA[HOUSTON]))

for event in events:
    e = events[event]
    event_uri = PREFIX + '#' + e['mission_timer']
    speaker = e['speaker']

    print("""
<%s> a sem:Event, prov:Activity ;
   sem:hasTimeStamp "%s" ;
   prov:value "%s" ;
   prov:wasQuotedFrom <%s> .
   """ % (
        event_uri, e['readable_mission_time'], e['spoken'], SPACELOG))

    if speaker:
        print_turtle_predicate_triple(event_uri, 'prov:wasAttributedTo', speaker)  # nopep8
        print_turtle_predicate_triple(event_uri, 'sem:hasActor', speaker)
        if speaker == LOVELL or speaker == SWIGERT or speaker == HAISE:
            print_turtle_predicate_triple(event_uri, 'sem:hasPlace', APOLLO13)
            print_turtle_predicate_triple(event_uri, 'prov:atLocation', APOLLO13)  # nopep8
        elif speaker == HOUSTON:
            print_turtle_predicate_triple(event_uri, 'sem:hasPlace', HOUSTON)
            print_turtle_predicate_triple(event_uri, 'prov:atLocation', HOUSTON)  # nopep8

    for p in e['participants']:
        print_turtle_predicate_triple(event_uri, 'sem:hasActor', p)
        print_turtle_predicate_triple(event_uri, 'prov:wasAssociatedWith', p)

    if 'terms' in e:
        for term in e['terms']:
            term_uri = PREFIX + '#' + term
            print_turtle_triple(term_uri, 'a', 'sem:Object')
            print_turtle_predicate_triple(event_uri, 'sem:hasActor', term_uri)
            if term in glossary:
                print(
                    '<%s> rdfs:label "%s"' % (
                        term_uri, glossary[term]['summary']
                    )
                )
