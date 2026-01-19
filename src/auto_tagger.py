"""
Auto-Tagging für Artikel basierend auf Inhalt und Titel
"""
import re
from typing import List

# Tag-Kategorien mit Keywords
TAG_RULES = {
    'Politik Österreich': [
        'österreich', 'wien', 'fpö', 'övp', 'spö', 'neos', 'grüne', 'kickl', 
        'nehammer', 'babler', 'meinl-reisinger', 'bundeskanzler', 'koalition',
        'nationalrat', 'regierung österreich', 'steiermark', 'bruck an der leitha',
        'salzburg', 'tirol', 'innsbruck', 'graz', 'kärnten', 'vorarlberg', 
        'oberösterreich', 'niederösterreich', 'burgenland', 'parlament wien',
        'hofburg', 'wiener', 'linz', 'klagenfurt'
    ],
    'Politik Deutschland': [
        'deutschland', 'berlin', 'afd', 'cdu', 'spd', 'grüne deutschland', 
        'scholz', 'merz', 'lindner', 'weidel', 'bundestag', 'bundesregierung',
        'bayern', 'münchen', 'hamburg', 'frankfurt', 'köln', 'stuttgart',
        'düsseldorf', 'bundesrat', 'bundespräsident', 'steinmeier', 'habeck',
        'baerbock', 'wadephul', 'linnemann', 'sellner', 'husch'
    ],
    'Politik USA': [
        'trump', 'usa', 'amerika', 'washington', 'weißes haus', 'white house',
        'präsident trump', 'republikaner', 'demokraten', 'biden', 'new york',
        'kalifornien', 'texas', 'florida', 'kongress', 'senat', 'vance',
        'pentagon', 'cia', 'fbi', 'grönland', 'powell', 'bessent', 'wallstreet'
    ],
    'Politik EU': [
        'eu ', 'europa', 'europäisch', 'brüssel', 'eu-kommission', 'europaparlament',
        'eu-', 'europäische union', 'ursula von der leyen', 'nato', 'mercosur',
        'europarat', 'straßburg', 'europäisches parlament', 'europäische zentralbank',
        'ezb', 'schengen', 'euratom', 'europol', 'frontex'
    ],
    'Satire': [
        'fake daily', 'chefredakteur', 'kaiser', 'in eigener sache'
    ],
    'Technologie': [
        'ki ', 'künstliche intelligenz', 'elon musk', 'spacex', 'tesla', 'google',
        'gemini', 'chatgpt', 'technologie', 'software', 'hardware', 'internet',
        'digital', 'computer', 'smartphone', 'apple', 'microsoft', 'meta',
        'facebook', 'instagram', 'tiktok', 'twitter', 'x.com', 'silicon valley',
        'cyber', 'hacker', 'datenschutz', 'cloud', 'server', 'roboter',
        'drohne', 'satellit', 'app', 'bitcoin', 'krypto', 'blockchain',
        'algorithmus', 'nvidia', 'intel', 'samsung', 'huawei'
    ],
    'Wirtschaft': [
        'wirtschaft', 'börse', 'aktien', 'unternehmen', 'firma', 'insolvenz',
        'pleite', 'geld', 'euro', 'inflation', 'steuer', 'benko', 'dax', 'dow',
        'wallstreet', 'nasdaq', 'freihandel', 'zoll', 'zölle', 'handel',
        'export', 'import', 'konjunktur', 'rezession', 'bruttoinlandsprodukt',
        'bip', 'arbeitslos', 'lohn', 'gehalt', 'mindestlohn', 'tarif',
        'gewerkschaft', 'streik', 'konzern', 'startup', 'investition',
        'bankrott', 'fusion', 'übernahme', 'gold', 'silber', 'rohstoff',
        'kupfer', 'öl', 'gas', 'immobilien', 'wohnung', 'miete', 'baubranche',
        'einzelhandel', 'konsum', 'umsatz', 'gewinn', 'verlust', 'dividende',
        'oxfam', 'milliardär', 'vermögen', 'saks', 'warenhaus', 'geberit', 'sika'
    ],
    'Wissenschaft': [
        'wissenschaft', 'forschung', 'studie', 'experte', 'professor', 'universität',
        'klima', 'erderwärmung', 'physik', 'chemie', 'biologie', 'genetik',
        'genom', 'dna', 'astronomie', 'weltraum', 'nasa', 'esa', 'mars',
        'mond', 'planet', 'galaxie', 'teleskop', 'mikrobiologie', 'virus',
        'bakterie', 'evolution', 'ökologie', 'umwelt', 'natur', 'artenvielfalt',
        'biodiversität', 'aussterben', 'tier', 'pflanze', 'ozean', 'meer',
        'meeresspiegelanstieg', 'gletscher', 'klimawandel', 'treibhausgas',
        'co2', 'methan', 'ozon', 'antarktis', 'arktis', 'permafrost',
        'hochseeschutz', 'schildkröte', 'wal', 'delfin', 'korallenriff'
    ],
    'Energie': [
        'energie', 'strom', 'solar', 'photovoltaik', 'windkraft', 'atomkraft',
        'akw', 'kernkraft', 'erneuerbare', 'stromausfall', 'blackout',
        'stromnetz', 'energiewende', 'brennstoff', 'kohle', 'braunkohle',
        'gaskraftwerk', 'kohlekraftwerk', 'wasserkraft', 'geothermie',
        'biomasse', 'biogas', 'energiespeicher', 'batterie', 'akkumulator',
        'wasserstoff', 'elektrolyse', 'brennstoffzelle', 'energieeffizienz',
        'wärmepumpe', 'fernwärme', 'heizung', 'dämmung', 'isolation',
        'gasspeicher', 'lng', 'pipeline', 'druschba', 'nord stream'
    ],
    'Medien': [
        'medien', 'presse', 'zeitung', 'fernsehen', 'orf', 'journalis', 
        'nachrichten', 'fake news', 'reporter', 'redakteur', 'verlag',
        'rundfunk', 'radio', 'podcast', 'streaming', 'netflix', 'amazon prime',
        'disney+', 'youtube', 'influencer', 'social media', 'zensur',
        'pressefreiheit', 'berichterstattung', 'interview', 'dokumentation',
        'live-ticker', 'breaking news', 'eilmeldung', 'sondersendung',
        'tagesschau', 'nzz', 'standard', 'krone', 'kurier', 'presse',
        'süddeutsche', 'faz', 'spiegel', 'bild', 'welt', 'zeit', 'guardian',
        'cnn', 'fox news', 'bbc', 'srf', 'zdf', 'ard', 'rtl', 'sat1', 'pro7'
    ],
    'Gesellschaft': [
        'gesellschaft', 'sozial', 'integration', 'migration', 'ausländer',
        'flüchtling', 'demo', 'protest', 'demonstration', 'kundgebung',
        'menschenrecht', 'diskriminierung', 'rassismus', 'sexismus',
        'gleichstellung', 'feminismus', 'lgbt', 'queer', 'pride',
        'inklusion', 'barrierefreiheit', 'behinderung', 'rente', 'pension',
        'altersarmut', 'kinderarmut', 'obdachlos', 'wohnungslos', 'tafel',
        'sozialhilfe', 'hartz iv', 'bürgergeld', 'kindergeld', 'familienpolitik',
        'bildung', 'schule', 'universität', 'studium', 'ausbildung',
        'jugend', 'generation z', 'millennials', 'boomer', 'rentner',
        'senioren', 'jugendliche', 'teenager', 'kinder', 'familie',
        'alleinerziehend', 'patchwork', 'hochzeit', 'scheidung', 'partnerschaft'
    ],
    'Gesundheit': [
        'gesundheit', 'medizin', 'arzt', 'krankenhaus', 'pflege', 'gesundheitssystem',
        'patient', 'behandlung', 'therapie', 'operation', 'chirurgie',
        'intensivstation', 'notaufnahme', 'ambulanz', 'hausarzt', 'facharzt',
        'apotheke', 'medikament', 'arzneimittel', 'impfung', 'vakzin',
        'corona', 'covid', 'pandemie', 'epidemie', 'virus', 'grippe',
        'influenza', 'erkältung', 'fieber', 'husten', 'schnupfen',
        'krebs', 'tumor', 'chemotherapie', 'bestrahlung', 'onkologie',
        'herz', 'herzinfarkt', 'schlaganfall', 'diabetes', 'bluthochdruck',
        'übergewicht', 'adipositas', 'ernährung', 'diät', 'abnehmen',
        'alkohol', 'sucht', 'droge', 'rauchen', 'nikotin', 'tabak',
        'mental health', 'psyche', 'depression', 'burnout', 'stress',
        'angststörung', 'psychiatrie', 'psychotherapie', 'trauma',
        'pflegeheim', 'altenheim', 'altenpflege', 'krankenpflege',
        'gesundheitsversorgung', 'krankenkasse', 'versicherung', 'pharma',
        'haut', 'transplantation', 'organ', 'spende', 'blut', 'plasma'
    ],
    'Justiz': [
        'gericht', 'richter', 'justiz', 'anwalt', 'klage', 'urteil', 'prozess',
        'staatsanwalt', 'verhaftung', 'strafverfahren', 'zivilprozess',
        'verwaltungsgericht', 'verfassungsgericht', 'oberstes gericht',
        'bundesgericht', 'berufung', 'revision', 'recht', 'gesetz',
        'paragraph', 'strafrecht', 'zivilrecht', 'verwaltungsrecht',
        'verfassungsrecht', 'völkerrecht', 'menschenrecht', 'grundrecht',
        'verurteilung', 'freispruch', 'strafe', 'haft', 'gefängnis',
        'haftstrafe', 'geldstrafe', 'bewährung', 'untersuchungshaft',
        'polizei', 'ermittlung', 'durchsuchung', 'festnahme', 'razzia',
        'verdächtig', 'täter', 'opfer', 'zeuge', 'aussage', 'beweis',
        'gutachten', 'sachverständig', 'forensik', 'kriminalistik',
        'korruption', 'betrug', 'unterschlagung', 'steuerhinterziehung',
        'geldwäsche', 'bestechung', 'bestechlichkeit', 'untreue',
        'missbrauch', 'vergewaltigung', 'mord', 'totschlag', 'körperverletzung',
        'diebstahl', 'raub', 'einbruch', 'vandalismus', 'sachbeschädigung',
        'pilnacek', 'wienwert', 'u-ausschuss', 'ibiza-affäre'
    ],
    'Militär': [
        'militär', 'armee', 'soldat', 'waffe', 'krieg', 'ukraine', 'russland',
        'putin', 'nato', 'verteidigung', 'bundeswehr', 'bundesheer',
        'streitkräfte', 'luftwaffe', 'marine', 'heer', 'panzer', 'kampfjet',
        'hubschrauber', 'drohne', 'rakete', 'artillerie', 'munition',
        'granate', 'bombe', 'sprengstoff', 'landmine', 'kampf', 'gefecht',
        'schlacht', 'offensive', 'angriff', 'verteidigung', 'rückzug',
        'waffenstillstand', 'friedensverhandlung', 'friedensvertrag',
        'kriegsverbrechen', 'völkermord', 'genozid', 'kriegsrecht',
        'genfer konvention', 'haager landkriegsordnung', 'un-charta',
        'syrien', 'assad', 'is', 'islamischer staat', 'terror', 'terrorismus',
        'al-qaida', 'taliban', 'hisbollah', 'hamas', 'israel', 'palästina',
        'gaza', 'westjordanland', 'iran', 'chamenei', 'revolution',
        'china', 'taiwan', 'nordkorea', 'südkorea', 'afghanistan', 'irak',
        'libyen', 'jemen', 'sudan', 'mali', 'sahel', 'wagner-gruppe',
        'söldner', 'militärputsch', 'staatsstreich', 'diktatur', 'autokrat',
        'diktator', 'regime', 'unterdrückung', 'repression', 'folter',
        'selenskyj', 'kiew', 'moskau', 'kreml', 'donbass', 'krim',
        'kurden', 'sdf', 'al-scharaa', 'tabka', 'raqa', 'damaskus'
    ],
    'Lebensmittel': [
        'lebensmittel', 'essen', 'nahrung', 'schnitzel', 'fleisch', 'laborfleisch',
        'vegetarisch', 'vegan', 'schokolade', 'restaurant', 'gastro',
        'gastronomie', 'koch', 'rezept', 'kochen', 'backen', 'küche',
        'bio', 'öko', 'regional', 'saisonal', 'landwirtschaft', 'bauer',
        'bauernhof', 'acker', 'feld', 'ernte', 'säen', 'pflügen',
        'milch', 'molkerei', 'käse', 'butter', 'joghurt', 'quark',
        'milchprodukt', 'laktose', 'kuhmilch', 'ziegenmilch', 'schafsmilch',
        'fleischersatz', 'tofu', 'seitan', 'tempeh', 'soja', 'erbsenprotein',
        'beyond meat', 'impossible burger', 'insekten', 'mehlwurm',
        'brot', 'brötchen', 'gebäck', 'kuchen', 'torte', 'konditorei',
        'bäckerei', 'gemüse', 'obst', 'salat', 'kartoffel', 'nudel',
        'reis', 'getreide', 'weizen', 'roggen', 'dinkel', 'hafer',
        'zucker', 'süß', 'salz', 'gewürz', 'kraut', 'kräuter',
        'wein', 'bier', 'spirituosen', 'whisky', 'wodka', 'gin',
        'weinberg', 'weingut', 'brauerei', 'destillerie', 'barista',
        'kaffee', 'tee', 'kakao', 'schokoladen', 'süßwaren',
        'fast food', 'burger', 'pizza', 'döner', 'pommes', 'currywurst',
        'lebensmittelsicherheit', 'hygiene', 'kontrolle', 'rückruf',
        'verbraucherschutz', 'mindesthaltbarkeit', 'verfallsdatum',
        'allergien', 'gluten', 'laktoseintoleranz', 'nussallergie',
        'gemüsestäbchen', 'apéro', 'nachhaltigkeit', 'verschwendung'
    ]
}


def generate_tags(title: str, content: str) -> List[str]:
    """Generiert Tags basierend auf Titel und Inhalt
    
    Args:
        title: Artikel-Titel
        content: Artikel-Inhalt
        
    Returns:
        Liste von generierten Tags
    """
    # Kombiniere Titel und Content für Analyse
    text_lower = (title + ' ' + content).lower()
    matched_tags = []
    
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if keyword in text_lower:
                matched_tags.append(tag)
                break  # Ein Match pro Tag-Kategorie reicht
    
    # Entferne Duplikate und sortiere
    return sorted(list(set(matched_tags)))


def add_auto_tags_if_empty(tags: List[str], title: str, content: str) -> List[str]:
    """Fügt automatische Tags hinzu, falls keine Tags angegeben sind
    
    Args:
        tags: Bestehende Tags (kann leer sein)
        title: Artikel-Titel
        content: Artikel-Inhalt
        
    Returns:
        Tags (entweder die bestehenden oder auto-generierte)
    """
    # Wenn bereits Tags vorhanden sind, diese zurückgeben
    if tags and len(tags) > 0:
        return tags
    
    # Ansonsten Auto-Tagging verwenden
    return generate_tags(title, content)
