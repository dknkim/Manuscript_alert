#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

import requests
import xml.etree.ElementTree as ET


def read_pmids_file(path: str) -> List[str]:
	if not os.path.isfile(path):
		raise FileNotFoundError(f"PMIDs file not found: {path}")
	with open(path, 'r', encoding='utf-8') as f:
		content = f.read().strip()
	# Try JSON {"pmids": [...]} first
	try:
		obj = json.loads(content)
		if isinstance(obj, dict) and isinstance(obj.get('pmids'), list):
			pmids = [str(x).strip() for x in obj['pmids'] if str(x).strip()]
			return pmids
	except Exception:
		pass
	# Fallback: newline separated
	pmids: List[str] = []
	for line in content.splitlines():
		line = line.strip()
		if line and line.lower().startswith('pmid:'):
			line = line.split(':', 1)[1].strip()
		if line:
			pmids.append(line)
	return pmids


def clean_text(s: str | None) -> str:
	if not s:
		return ''
	import re
	s = re.sub(r'<[^>]+>', '', s)
	s = re.sub(r'\s+', ' ', s.strip())
	return s


def fetch_pubmed_records(pmids: List[str]) -> List[Dict[str, Any]]:
	if not pmids:
		return []
	base = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
	params = {
		'db': 'pubmed',
		'id': ','.join(pmids),
		'retmode': 'xml',
	}
	r = requests.get(base, params=params, timeout=30)
	r.raise_for_status()
	root = ET.fromstring(r.content)
	recs: List[Dict[str, Any]] = []
	for a in root.findall('.//PubmedArticle'):
		medline = a.find('MedlineCitation')
		if medline is None:
			continue
		pmid = (medline.findtext('PMID') or '').strip()
		article = medline.find('Article')
		if article is None:
			continue
		title = clean_text(article.findtext('ArticleTitle'))
		abstract_nodes = article.findall('Abstract/AbstractText')
		if abstract_nodes:
			abstract = ' '.join([clean_text(''.join(n.itertext())) for n in abstract_nodes])
		else:
			abstract = ''
		journal = ''
		j = article.find('Journal')
		if j is not None:
			jt = j.findtext('Title') or j.findtext('ISOAbbreviation')
			journal = jt or ''
		pubdate = ''
		pd = article.find('Journal/JournalIssue/PubDate')
		if pd is not None:
			y = pd.findtext('Year') or ''
			m = pd.findtext('Month') or '1'
			d = pd.findtext('Day') or '1'
			month_map = {'Jan':'1','Feb':'2','Mar':'3','Apr':'4','May':'5','Jun':'6','Jul':'7','Aug':'8','Sep':'9','Oct':'10','Nov':'11','Dec':'12'}
			if m in month_map:
				m = month_map[m]
			try:
				y = int(y) if str(y).isdigit() else datetime.now().year
				m = int(m) if str(m).isdigit() else 1
				d = int(d) if str(d).isdigit() else 1
				pubdate = f"{y:04d}-{m:02d}-{d:02d}"
			except Exception:
				pubdate = ''
		recs.append({
			'pmid': pmid,
			'title': title,
			'abstract': abstract,
			'journal': journal,
			'published': pubdate,
			'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
			'source': 'PubMed',
		})
	return recs


def main() -> None:
	parser = argparse.ArgumentParser(description='Generate KB seed (title+abstract) from a PMIDs file')
	parser.add_argument('--pmids-file', required=True, help='Path to pmids.json or newline-separated list')
	parser.add_argument('--output', default=None, help='Output path (default: <dir_of_pmids_file>/kb_seed.json)')
	args = parser.parse_args()

	pmids = read_pmids_file(args.pmids_file)
	if not pmids:
		print('No PMIDs found in file.'); return

	records = fetch_pubmed_records(pmids)
	payload = {
		'project': os.path.basename(os.path.dirname(os.path.abspath(args.pmids_file))) or 'KB_project',
		'created_at': datetime.utcnow().isoformat() + 'Z',
		'pmids': pmids,
		'records_count': len(records),
		'records': records,
	}
	out_path = args.output or os.path.join(os.path.dirname(os.path.abspath(args.pmids_file)), 'kb_seed.json')
	with open(out_path, 'w', encoding='utf-8') as f:
		json.dump(payload, f, ensure_ascii=False, indent=2)
	print('Saved:', out_path)
	print('Count:', len(records))


if __name__ == '__main__':
	main() 