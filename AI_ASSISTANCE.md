<img alt="Tiefer Lab" src="docs/assets/header.png" width="100%">

# AI assistance

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

For everyone who opens an issue or a pull request in Tiefer Lab, and for the maintainers who review them. This document owns the rule for disclosing AI-assisted systems, the data rules for such systems, the labelling of AI-generated content, and the list of EU legal texts that the issue forms and pull request templates refer to. It is not legal advice.

---

## 1. Scope

This policy applies to every issue, pull request, commit, document and file submitted to this repository, by anyone, maintainers included, and to the comments and reviews on them.

An AI-assisted system, in this policy, is any software that writes, changes, reviews, translates, summarises or analyses text, code, data or images with a machine-learning model on behalf of the person using it: chat assistants, code completion in an editor, command-line agents, translation and summarising tools, and models built into other products. Tools that do not use such a model, for example `ruff format`, a spell-checker based on a word list or a search engine's list of results, are not covered.

The EU AI Act defines "AI system" in its own words (section 7); the term of this policy is narrower and is used only here.

---

## 2. Disclosure rule

1. Every AI-assisted system used to write, change, review, translate or analyse anything in an issue or a pull request is disclosed in the "AI assistance disclosure" section of the issue form or pull request template.
2. For each system, the disclosure names: the provider, the developer of the model, the product or tool and its version, the model name, the exact model version or identifier and the date it was used, how it was accessed, where the model ran, what it was used for, what content it was given, the share of the submitted content it produced, how its output was reviewed and verified, whether the tool's terms allow the output to be submitted under MPL 2.0, and whether the output was checked for reproduced third-party material.
3. "No AI-assisted system was used" is a disclosure too, and is given in the same section.
4. A value that is not known is written `not known`; it is never guessed.
5. A system used after the issue or pull request was opened, for example for a later commit or a review comment, is disclosed in a new comment with the same fields.
6. How a commit pushed to `main` outside a pull request carries its disclosure is an open decision (section 9).

---

## 3. Responsibility

- The person who submits an issue, a commit or a pull request is responsible for every line of it, whoever or whatever wrote the line.
- Submit only what you have read and understood. A reviewer may ask you to explain any line.
- Content produced with an AI-assisted system passes the same gates of [POLICY.md](POLICY.md) as any other content. A number that an AI-assisted system wrote, estimated, rounded or summarised is not a measured value and is never entered as one ([POLICY.md](POLICY.md), gate 1).
- A source or citation suggested by an AI-assisted system is opened and read before it is cited; a source that could not be opened is not cited ([docs/STYLE.md](docs/STYLE.md), section 8).
- The tests and checks of [CONTRIBUTING.md](CONTRIBUTING.md), section 3, apply unchanged.

---

## 4. Data rules

Never give an AI-assisted system:

1. credentials, tokens, keys or the content of a `.env` file ([SECURITY.md](SECURITY.md), section 7);
2. personal data, your own included, or any special category of personal data (section 7, GDPR Articles 4(1) and 9);
3. confidential material of a partner, a customer or another third party;
4. an unreported security problem ([SECURITY.md](SECURITY.md), section 2).

Further rules:

- Remove CSC project identifiers, user names and absolute paths from logs and report files before you give them to an AI-assisted system; `tests/test_public_hygiene.py` lists the patterns that must not appear in the repository.
- Give a system only the content it needs for the task.
- For code that is not yet public, prefer a system that runs on your own hardware or with a provider in the EU or EEA, and say where it ran in the disclosure.
- Personal data sent to a system that runs outside the EU or EEA is a transfer under Chapter V of the GDPR (Articles 44 to 49). Rule 2 above avoids such transfers.

---

## 5. Licence and provenance

- Contributions are licensed under MPL 2.0, and the confirmations of [CONTRIBUTING.md](CONTRIBUTING.md), section 9, apply to content produced with an AI-assisted system as to any other content.
- Read the terms of the tool you used. Submit its output only if those terms allow you to submit it under MPL 2.0; if you are not sure, say so in the disclosure and do not submit the output until a maintainer has answered.
- Check output for reproduced third-party code or text, for example by searching for distinctive lines. Where a match is found, keep the original licence notice and attribution, and only if that licence is compatible with MPL 2.0; otherwise remove the match.
- Data follows gate 6 of [POLICY.md](POLICY.md). For text or data collected from the web, record whether its rightholders reserved text and data mining (Directive (EU) 2019/790, Article 4(3), section 7).

---

## 6. Labelling

AI-generated text, images, audio or video published from this repository are labelled as AI-generated, in all cases, also where the law would not require it:

- an issue or a pull request carries its disclosure (section 2);
- a Markdown file that an AI-assisted system drafted in whole or in large part says so in the changelog line of that change;
- a figure, image, audio or video file produced by an AI-assisted system says so in its caption, alt text or the document that links it, and is never presented as an observation or as evidence ([ACCEPTABLE_USE.md](ACCEPTABLE_USE.md), section 2).

This rule follows the purpose of EU AI Act Article 50: people should be able to tell when content was generated or manipulated by an AI system. It does not say that Article 50 applies to this repository.

---

## 7. Regulatory references

The texts were read on EUR-Lex on 7 October 2026: the GDPR in the consolidated version of 4 May 2016 [2], the AI Act in the consolidated version of 27 July 2026, which includes the amendments of Regulation (EU) 2026/1744 [3], and Directive (EU) 2019/790 as published [4]. The plain meaning column summarises; the text on EUR-Lex is the reference. This table does not say that any rule of this repository makes anyone meet any of these laws, and it does not say whether a law applies to this repository, to a contributor or to a tool.

| Article | Official title | Plain meaning | Source | Date read |
| :--- | :---: | :---: | :---: | :---: |
| **Regulation (EU) 2016/679 (GDPR)** | | | | |
| Article 4(1) | Definitions | "personal data" is any information relating to an identified or identifiable natural person, for example by a name, an online identifier or location data | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 4(2) | Definitions | "processing" is any operation on personal data, such as collection, storage, use, disclosure, erasure or destruction | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 5(1)(c) | Principles relating to processing of personal data | data minimisation: personal data are adequate, relevant and limited to what is necessary for the purposes of the processing | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 5(1)(f) | Principles relating to processing of personal data | integrity and confidentiality: personal data are processed with appropriate security, including protection against unauthorised or unlawful processing and accidental loss | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 6 | Lawfulness of processing | processing is lawful only if and to the extent that at least one of the bases listed in the article applies | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 9 | Processing of special categories of personal data | processing of data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs or trade union membership, and of genetic data, biometric data for unique identification, health data or data on sex life or sexual orientation, is prohibited unless an exception of paragraph 2 applies | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 13 | Information to be provided where personal data are collected from the data subject | when the controller collects personal data from the person, it gives the person the information listed, such as its identity and the purposes of the processing | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 14 | Information to be provided where personal data have not been obtained from the data subject | the same duty to inform, where the personal data come from another source | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 17 | Right to erasure ("right to be forgotten") | the person has the right to obtain erasure of their personal data without undue delay where one of the listed grounds applies | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 25 | Data protection by design and by default | the controller implements appropriate technical and organisational measures, and by default processes only the personal data necessary for each specific purpose | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 28 | Processor | a controller uses only processors that give sufficient guarantees; processing by a processor is governed by a contract or other legal act | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Article 32 | Security of processing | the controller and the processor implement measures to ensure a level of security appropriate to the risk | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| Chapter V, Articles 44 to 49 | Transfers of personal data to third countries or international organisations | a transfer of personal data to a country outside the EU, or to an international organisation, takes place only under the conditions of the chapter: an adequacy decision (45), appropriate safeguards (46), binding corporate rules (47) or a derogation for a specific situation (49); Article 48 covers transfers not authorised by Union law | [EUR-Lex, CELEX 02016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504) | 7 October 2026 |
| **Regulation (EU) 2024/1689 (AI Act)** | | | | |
| Article 2(6) and 2(8) | Scope | the regulation does not apply to AI systems or models, including their output, specifically developed and put into service for the sole purpose of scientific research and development (6), nor to research, testing or development before an AI system or model is placed on the market or put into service; testing in real world conditions is not covered by that exclusion (8) | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 3(1) | Definitions | "AI system": a machine-based system designed to operate with varying levels of autonomy that infers, from the input it receives, how to generate outputs such as predictions, content, recommendations or decisions | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 3(3) | Definitions | "provider": a person or body that develops an AI system or a general-purpose AI model, or has one developed, and places it on the market or puts it into service under its own name or trademark, whether for payment or free of charge | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 3(4) | Definitions | "deployer": a person or body using an AI system under its authority, except in a personal non-professional activity | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 3(9) | Definitions | "placing on the market": the first making available of an AI system or a general-purpose AI model on the Union market | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 3(11) | Definitions | "putting into service": the supply of an AI system for first use directly to the deployer, or for own use, in the Union for its intended purpose | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 3(63) | Definitions | "general-purpose AI model": a model that displays significant generality and can competently perform a wide range of distinct tasks, except models used for research, development or prototyping before they are placed on the market | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 4 | AI literacy | as amended by Regulation (EU) 2026/1744: providers and deployers take measures to support the development of AI literacy of their staff and of others who operate AI systems on their behalf; no specific level is required of any individual | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 5 | Prohibited AI practices | lists AI practices that are prohibited, among them manipulative or deceptive techniques that materially distort behaviour, social scoring, untargeted scraping of facial images, and certain uses of biometric systems; points (ba) and (bb), on generated intimate images of identifiable persons and on material within the meaning of Directive 2011/93/EU, were added by Regulation (EU) 2026/1744 | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 50 | Transparency obligations for providers and deployers of certain AI systems | providers of AI systems that generate synthetic audio, image, video or text mark the output in a machine-readable format (2); deployers disclose deep fakes, and disclose AI-generated or manipulated text published to inform the public on matters of public interest unless it had human review or editorial control and someone holds editorial responsibility (4) | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 53 | Obligations for providers of general-purpose AI models | providers of general-purpose AI models keep technical documentation, inform downstream providers, put in place a policy to comply with Union copyright law that identifies and respects reservations under Article 4(3) of Directive (EU) 2019/790 (point (c)), and publish a summary of the training content (point (d)) | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| Article 113 | Entry into force and application | the dates from which each part applies; listed below this table | [EUR-Lex, CELEX 02024R1689](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727) | 7 October 2026 |
| **Directive (EU) 2019/790** | | | | |
| Article 4 | Exception or limitation for text and data mining | Member States allow reproductions and extractions of lawfully accessible works for text and data mining (1), on condition that the rightholders have not expressly reserved that use in an appropriate manner, such as machine-readable means for content made publicly available online (3); a directive applies through the national law of each Member State | [EUR-Lex, CELEX 32019L0790](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019L0790) | 7 October 2026 |

The AI Act applies in stages (Article 113, as amended by Regulation (EU) 2026/1744):

| Part | Applies from |
| :--- | :---: |
| Chapters I and II (general provisions, including Articles 2 to 4, and prohibited practices, Article 5) | 2 February 2025 |
| Article 5(1), first subparagraph, points (ba) and (bb), and Article 5(1a) and (1b) | 2 December 2026 |
| Chapter III Section 4, Chapters V, VII and XII, and Article 78, except Article 101 | 2 August 2025 |
| Articles 102 to 110 | 27 July 2026 |
| The rest of the regulation, including Chapter IV (Article 50) | 2 August 2026 |
| Chapter III Sections 1 to 3, except Article 6(5), for high-risk systems under Article 6(2) and Annex III | 2 December 2027 |
| Chapter III Sections 1 to 3, except Article 6(5), for high-risk systems under Article 6(1) and Annex I | 2 August 2028 |

Issues and pull requests on GitHub are public. GitHub processes the personal data of its users under its own privacy statement [1].

---

## 8. Breaches

| Breach | What happens |
| :--- | :---: |
| An AI-assisted system was used and not disclosed | the submitter adds the missing disclosure in a comment; a maintainer may pause the review until it is there |
| A credential was given to an AI-assisted system or posted | revoke it first, at its issuer, then follow [SECURITY.md](SECURITY.md), section 7 |
| Personal data of someone else, or special category data, was posted | a maintainer hides or edits the content ([CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), section 7) and asks the submitter to confirm what was shared and where |
| An AI-generated number was entered as measured | the value is removed and the change is reverted under gate 1 of [POLICY.md](POLICY.md) |
| Repeated or deliberate breaches | the enforcement steps of [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), section 7 |

---

## 9. Review

This policy is reviewed when a law in section 7 or its dates of application change, and at least once a year. A change is a policy change ([GOVERNANCE.md](GOVERNANCE.md), section 2) and gets a changelog line.

Open decisions of the founder:

| Decision | Status |
| :--- | :---: |
| How maintainers disclose AI-assisted systems in commits they push directly to `main`, outside a pull request | open |
| Whether content added before this policy is disclosed or labelled | open |

---

## 10. Sources

1. GitHub General Privacy Statement, GitHub, effective 27 April 2026, https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement, accessed 7 October 2026.
2. Regulation (EU) 2016/679 (General Data Protection Regulation), consolidated text 02016R0679 of 4 May 2016, EUR-Lex, https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504, accessed 7 October 2026.
3. Regulation (EU) 2024/1689 (Artificial Intelligence Act), consolidated text 02024R1689 of 27 July 2026, EUR-Lex, https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727, accessed 7 October 2026.
4. Directive (EU) 2019/790 on copyright and related rights in the Digital Single Market, EUR-Lex, https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019L0790, accessed 7 October 2026.

---

## Changelog

- 7 October 2026: section 4, rule 2 covers all personal data, the contributor's own included, as the acknowledgement in the issue forms and pull request templates states it.
- 7 October 2026: first version: scope, disclosure rule, responsibility, data rules, licence and provenance, labelling, the regulatory references read on EUR-Lex, breaches and review.
