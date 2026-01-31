# =========================
# Boilerplate patterns
# =========================

FILE_PATTERNS = {
    "compete2030": [
        r"Saltar para o conteúdo principal da página.*?Modo claro",
        r"Saltar para o conteúdo principal.*?Início",
        r"Esta página foi útil para si\?.*?A carregar",
        r"© COMPETE 2030.*$"
    ],
    "centro2030": [
        r"Programas do Portugal 2030\s+PESSOAS 2030.*?Antifraude",
        r"Programas do Portugal 2030.*?Avisos de concurso",
        r"© 2023 Centro 2030.*$"
    ],
    "alentejo2030": [
        r"Programas do Portugal 2030.*?Regras de Comunicação",
        r"Ajuda\s+O Alentejo 2030.*?Regras de Comunicação",
        r"Este site utiliza cookies.*$"
    ],
    "algarve2030": [
        r"Programas do Portugal 2030.*?Área Reservada",
        r"Este site utiliza cookies.*$"
    ],
    "lisboa2030": [
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
    "iapmei": [
        r"Este sítio utiliza cookies de terceiros.*?Recebera uma password nova no seu email de registo\.\s*E-mail"
    ]
}

NAV_WORDS = {
    "início", "contactos", "eventos", "notícias", "ajuda",
    "menu", "seguir", "newsletter", "subscreva",
    "pt", "en", "login", "registar", "pesquisar"
}

COMMON_PT_VERBS = {
    "é", "são", "foi", "foram", "ser", "estar", "tem", "têm",
    "permite", "permitir", "visa", "promove", "apoia",
    "inclui", "consiste", "define", "aplica"
}


FORBIDDEN_TOPICS = {
    "cookies",
    "termos e condições",
    "política de privacidade",
    "ligações úteis"
}
