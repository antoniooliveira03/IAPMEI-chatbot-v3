# =========================
# Boilerplate patterns
# =========================

FILE_PATTERNS = {
    "compete2030": [
        r"Saltar para o conteúdo principal.*?Início",
        r"Esta página foi útil para si\?.*?A carregar",
        r"© COMPETE 2030.*$"
    ],
    "centro2030": [
        r"Programas do Portugal 2030.*?Avisos de concurso",
        r"© 2023 Centro 2030.*$"
    ],
    "alentejo_portugal2030": [
        r"Programas do Portugal 2030.*?Regras de Comunicação",
        r"Este site utiliza cookies.*$"
    ],
    "algarve_portugal2030": [
        r"Programas do Portugal 2030.*?Área Reservada",
        r"Este site utiliza cookies.*$"
    ],
    "lisboa_portugal2030": [
        r"Programas do Portugal 2030.*?Plano Anual de Avisos",
        r"Este site utiliza cookies.*$"
    ],
    "norte2030": [
        r"Ir para o conteúdo principal.*?Pesquisar",
        r"© 2024 NORTE 2030.*$"
    ],
    "portugal2030": [
        r"Saltar para o conteúdo principal.*?Plano Anual de Avisos",
        r"Este site utiliza cookies.*$"
    ],
    "FTJ": [
        r"Top This site is managed by the Publications Office of the European Union.*?\n\n",
        r"Need help\?.*?Follow us.*?\n\n",
        r"Legal notice.*?Cookies policy.*?Accessibility.*?Privacy statement.*?\n\n",
        r"EU institutions.*?European Parliament.*?European Commission.*?\n\n",
        r"Switch to mobile.*?Switch to desktop.*?\n\n"
    ]
}

BOILERPLATE_FTJ = (
    "Top This site is managed by the Publications Office of the European Union "
    "Need help? Help pages Contact Sitemap Follow us X Legal Legal notice Cookies policy "
    "Accessibility Privacy statement Information About EUR-Lex Newsletter Useful links Other services "
    "European Data EU tenders EU research results EU Whoiswho EU publications N-Lex EU Law Tracker "
    "Discover more on europa.eu Contact the EU Call us 00 800 6 7 8 9 10 11 Use other telephone options "
    "Write to us via our contact form Meet us at one of the EU centres Social media Search for EU social media channels "
    "Legal Languages on our websites Privacy policy Legal notice Cookies EU institutions European Parliament "
    "European Council Council of the European Union European Commission Court of Justice of the European Union (CJEU) "
    "European Central Bank (ECB) European Court of Auditors European External Action Service (EEAS) "
    "European Economic and Social Committee European Committee of Regions (CoR) European Investment Bank "
    "European Ombudsman European Data Protection Supervisor (EDPS) European Data Protection Board "
    "European Personnel Selection Office Publications Office of the European Union Agencies "
    "Switch to mobile Switch to desktop"
    "bg български es Español cs Čeština da Dansk de Deutsch et Eesti keel el Ελληνικά "
    "en English fr Français ga Gaeilge hr Hrvatski it Italiano lv Latviešu valoda lt Lietuvių kalba "
    "hu Magyar mt Malti nl Nederlands pl Polski pt Português ro Română sk Slovenčina sl Slovenščina "
    "fi Suomi sv Svenska EUR-Lex Access to European Union law <a href=\\\"https://eur-lex.europa.eu/content/help/eurlex-content/experimental-features.html\\\" "
    "target=\\\"_blank\\\">More about the experimental features corner</a> Experimental features × "
    "Choose the experimental features you want to try Do you want to help improving EUR-Lex? "
    "This is a list of experimental features that you can enable. These features are still under development; "
    "they are not fully tested, and might reduce EUR-Lex stability. Don't forget to give your feedback! "
    "Warning! Experimental feature conflicts detected. Replacement of CELEX identifiers by short titles - experimental feature. "
    "It replaces clickable CELEX identifiers of treaties and case-law by short titles. Visualisation of document relationships. "
    "It displays a dynamic graph with relations between the act and related documents. "
    "It is currently only available for legal acts. Deep linking. "
    "It enables links to other legal acts referred to within the documents. "
    "It is currently only available for documents smaller than 900 KB. Apply EUR-Lex Access to European Union law "
    "This document is an excerpt from the EUR-Lex website You are here EUROPA EUR-Lex home EUR-Lex - 52019DC0640 - EN "
    "Help Print Menu EU law Treaties Treaties currently in force Founding Treaties Accession Treaties Other treaties and protocols "
    "Chronological overview Legal acts Consolidated texts International agreements Preparatory documents EFTA documents Lawmaking procedures "
    "Summaries of EU legislation Browse by EU institutions European Parliament European Council Council of the European Union "
    "European Commission Court of Justice of the European Union European Central Bank European Court of Auditors "
    "European Economic and Social Committee European Committee of the Regions Browse by EuroVoc EU case-law Case-law Reports of cases "
    "Directory of case-law Official Journal Access to the Official Journal Official Journal L series daily view "
    "Official Journal C series daily view Browse the Official Journal Legally binding printed editions Special edition "
    "National law and case-law National transposition National case-law JURE case-law Information Themes in focus EUR-Lex developments "
    "Statistics ELI register What is ELI ELI background Why implement ELI Countries implementing ELI Testimonials Implementing ELI Glossary "
    "EU budget online Quick search Use quotation marks to search for an \\\"exact phrase\\\". Append an asterisk ( * ) to a search term "
    "to find variations of it (transp *, 32019R * ). Use a question mark (? ) instead of a single character in your search term "
    "to find variations of it (ca? e finds case, cane, care). Search tips Need more search options? Use the Advanced search "
    "Document 52019DC0640 Help Print Text Document information Document summary Permanent link Download notice Save to My items "
    "Create an email alert Create an RSS alert ​ COMMUNICATION FROM THE COMMISSION TO THE EUROPEAN PARLIAMENT, "
    "THE EUROPEAN COUNCIL, THE COUNCIL, THE EUROPEAN ECONOMIC AND SOCIAL COMMITTEE AND THE COMMITTEE OF THE REGIONS "
    "The European Green Deal COMUNICAÇÃO DA COMISSÃO AO PARLAMENTO EUROPEU, AO CONSELHO EUROPEU, AO CONSELHO, AO COMITÉ ECONÓMICO "
    "E SOCIAL EUROPEU E AO COMITÉ DAS REGIÕES Pacto Ecológico Europeu COMUNICAÇÃO DA COMISSÃO AO PARLAMENTO EUROPEU, AO CONSELHO "
    "EUROPEU, AO CONSELHO, AO COMITÉ ECONÓMICO E SOCIAL EUROPEU E AO COMITÉ DAS REGIÕES Pacto Ecológico Europeu COM/2019/640 final "
)


BOILERPLATE_FAMI_IGFV = (
    "Top This site is managed by the Publications Office of the European Union "
    "Need help? Help pages Contact Sitemap Follow us X Legal Legal notice Cookies policy "
    "Accessibility Privacy statement Information About EUR-Lex Newsletter Useful links Other services "
    "European Data EU tenders EU research results EU Whoiswho EU publications N-Lex EU Law Tracker "
    "Discover more on europa.eu Contact the EU Call us 00 800 6 7 8 9 10 11 Use other telephone options "
    "Write to us via our contact form Meet us at one of the EU centres Social media Search for EU social media channels "
    "Legal Languages on our websites Privacy policy Legal notice Cookies EU institutions European Parliament "
    "European Council Council of the European Union European Commission Court of Justice of the European Union (CJEU) "
    "European Central Bank (ECB) European Court of Auditors European External Action Service (EEAS) "
    "European Economic and Social Committee European Committee of Regions (CoR) European Investment Bank "
    "European Ombudsman European Data Protection Supervisor (EDPS) European Data Protection Board "
    "European Personnel Selection Office Publications Office of the European Union Agencies "
    "Switch to mobile Switch to desktop"
)