#!/usr/bin/env python3
"""
Test für kontextbezogenes Auto-Tagging
Zeigt, dass mehrdeutige Begriffe korrekt behandelt werden
"""
from src.auto_tagger import generate_tags

def test_gesundheit_context():
    """Test: Gesundheit-Kategorie mit mehrdeutigen Begriffen"""
    
    print("=" * 80)
    print("GESUNDHEIT-TESTS")
    print("=" * 80)
    
    tests = [
        {
            'name': 'Organ des Strafvollzugs',
            'title': 'Reformvorschläge für das Strafvollzugssystem',
            'content': 'Das Organ des Strafvollzugs arbeitet an neuen Konzepten für die Rehabilitation von Straftätern.',
            'expect_not': 'Gesundheit',
            'expect_has': 'Justiz'
        },
        {
            'name': 'Organspende (medizinisch)',
            'title': 'Organspende rettet Leben',
            'content': 'Die Transplantation eines Spenderorgans kann für viele Patienten lebensrettend sein.',
            'expect_has': 'Gesundheit'
        },
        {
            'name': 'Herz aus Stein (Metapher)',
            'title': 'Politiker zeigt keine Emotionen',
            'content': 'Der Politiker hat ein Herz aus Stein und ignoriert die Sorgen der Bürger.',
            'expect_not': 'Gesundheit'
        },
        {
            'name': 'Herzinfarkt (medizinisch)',
            'title': 'Steigende Herzinfarkt-Zahlen',
            'content': 'Die Zahl der Herzinfarkte nimmt zu. Ärzte empfehlen mehr Bewegung.',
            'expect_has': 'Gesundheit'
        },
        {
            'name': 'Blutbad (Gewalt)',
            'title': 'Konflikt eskaliert',
            'content': 'Der Konflikt endet in einem Blutbad. Viele Menschen wurden verletzt.',
            'expect_not': 'Gesundheit'
        },
        {
            'name': 'Blutspende (medizinisch)',
            'title': 'Krankenhaus ruft zu Blutspenden auf',
            'content': 'Das Krankenhaus braucht dringend mehr Blutspenden für Notfälle.',
            'expect_has': 'Gesundheit'
        },
        {
            'name': 'Wirtschaftskammer (Institution)',
            'title': 'Wirtschaftskammer fordert Reformen',
            'content': 'Die Wirtschaftskammer kritisiert die neue Steuerpolitik der Regierung.',
            'expect_not': 'Gesundheit'
        },
        {
            'name': 'Herzkammer (medizinisch)',
            'title': 'Probleme mit der Herzkammer',
            'content': 'Die linke Herzkammer pumpt nicht richtig. Operation notwendig.',
            'expect_has': 'Gesundheit'
        },
        {
            'name': 'Gefängniszelle (Justiz)',
            'title': 'Überfüllte Gefängnisse',
            'content': 'Die Zelle ist nur 6 Quadratmeter groß und für zwei Häftlinge vorgesehen.',
            'expect_not': 'Gesundheit'
        },
        {
            'name': 'Stammzelle (medizinisch)',
            'title': 'Stammzellenforschung macht Fortschritte',
            'content': 'Neue Therapien mit Stammzellen könnten vielen Patienten helfen.',
            'expect_has': 'Gesundheit'
        },
        {
            'name': 'Computer-Virus (Technologie)',
            'title': 'Neuer Virus bedroht Computer',
            'content': 'Ein gefährlicher Computer-Virus verbreitet sich über E-Mails.',
            'expect_not': 'Gesundheit',
            'expect_has': 'Technologie'
        },
        {
            'name': 'Grippe-Virus (medizinisch)',
            'title': 'Grippe-Welle rollt an',
            'content': 'Das Influenza-Virus breitet sich aus. Impfung wird empfohlen.',
            'expect_has': 'Gesundheit'
        },
        {
            'name': 'Wirtschaftliche Schocktherapie',
            'title': 'IWF empfiehlt harte Reformen',
            'content': 'Die Schocktherapie für die Wirtschaft soll die Inflation bekämpfen.',
            'expect_not': 'Gesundheit'
        },
        {
            'name': 'Psychotherapie (medizinisch)',
            'title': 'Therapieplätze fehlen',
            'content': 'Viele Patienten warten monatelang auf einen Psychotherapie-Platz.',
            'expect_has': 'Gesundheit'
        },
        {
            'name': 'Kulturszene (Gesellschaft)',
            'title': 'Kultur in der Krise',
            'content': 'Die Kultur leidet unter Sparmaßnahmen. Theater und Museen schließen.',
            'expect_not': 'Gesundheit'
        },
        {
            'name': 'Bakterienkultur (medizinisch)',
            'title': 'Neue Antibiotika-Resistenz entdeckt',
            'content': 'Die Bakterienkultur zeigt Resistenz gegen alle gängigen Antibiotika.',
            'expect_has': 'Gesundheit'
        },
    ]
    
    run_tests(tests)

def test_wirtschaft_context():
    """Test: Wirtschaft-Kategorie mit mehrdeutigen Begriffen"""
    
    print("\n" + "=" * 80)
    print("WIRTSCHAFT-TESTS")
    print("=" * 80)
    
    tests = [
        {
            'name': 'Parkbank (keine Wirtschaft)',
            'title': 'Neue Parkbänke aufgestellt',
            'content': 'Die Stadt hat neue Sitzbänke im Park aufgestellt.',
            'expect_not': 'Wirtschaft'
        },
        {
            'name': 'Nationalbank (Wirtschaft)',
            'title': 'Nationalbank erhöht Zinsen',
            'content': 'Die österreichische Nationalbank hebt den Leitzins an.',
            'expect_has': 'Wirtschaft'
        },
        {
            'name': 'Zahnkrone (Gesundheit)',
            'title': 'Teure Zahnbehandlung',
            'content': 'Die neue Zahnkrone kostet 800 Euro.',
            'expect_has': 'Gesundheit'
            # Wirtschaft ist auch OK wegen Kostenaspekt
        },
        {
            'name': 'Kronenzeitung (Medien)',
            'title': 'Krone berichtet über Skandal',
            'content': 'Die Kronen Zeitung deckt neue Details auf.',
            'expect_has': 'Medien',
            'expect_not': 'Wirtschaft'
        },
        {
            'name': 'Goldmedaille (Sport)',
            'title': 'Österreich gewinnt Gold',
            'content': 'Der Skifahrer holte die Goldmedaille bei Olympia.',
            'expect_not': 'Wirtschaft'
        },
        {
            'name': 'Goldpreis (Wirtschaft)',
            'title': 'Gold erreicht Rekordhoch',
            'content': 'Der Goldpreis steigt auf über 2000 Dollar pro Unze.',
            'expect_has': 'Wirtschaft'
        },
        {
            'name': 'Militärische Unternehmung',
            'title': 'Offensive in der Region',
            'content': 'Das Militär startet eine neue Unternehmung gegen die Rebellen.',
            'expect_not': 'Wirtschaft'
        },
        {
            'name': 'Unternehmensgewinn',
            'title': 'Rekordgewinn für Konzern',
            'content': 'Das Unternehmen meldet einen Gewinn von 2 Milliarden Euro.',
            'expect_has': 'Wirtschaft'
        },
    ]
    
    run_tests(tests)

def test_andere_kategorien():
    """Test: Andere Kategorien mit mehrdeutigen Begriffen"""
    
    print("\n" + "=" * 80)
    print("ANDERE KATEGORIEN-TESTS")
    print("=" * 80)
    
    tests = [
        {
            'name': 'Filmstudio (keine Wissenschaft)',
            'title': 'Neues Filmstudio eröffnet',
            'content': 'Ein großes Filmstudio für Hollywood-Produktionen öffnet in Wien.',
            'expect_not': 'Wissenschaft'
        },
        {
            'name': 'Wissenschaftliche Studie',
            'title': 'Neue Klimastudie veröffentlicht',
            'content': 'Eine umfassende Studie zeigt die Folgen des Klimawandels.',
            'expect_has': 'Wissenschaft'
        },
        {
            'name': 'Solarsystem (Astronomie)',
            'title': 'Neuer Planet entdeckt',
            'content': 'Astronomen finden einen neuen Planeten in einem fernen Solarsystem.',
            'expect_not': 'Energie'
        },
        {
            'name': 'Solaranlage (Energie)',
            'title': 'Solarenergie boomt',
            'content': 'Immer mehr Haushalte installieren Solaranlagen auf dem Dach.',
            'expect_has': 'Energie'
        },
        {
            'name': 'Tränengas (Militär/Polizei)',
            'title': 'Polizei setzt Tränengas ein',
            'content': 'Bei der Demo wurde Tränengas gegen die Demonstranten eingesetzt.',
            'expect_not': 'Energie'
        },
        {
            'name': 'Gaspreise (Energie)',
            'title': 'Gaspreise steigen weiter',
            'content': 'Die Kosten für Erdgas erreichen ein neues Rekordhoch.',
            'expect_has': 'Energie'
        },
        {
            'name': 'Druckpresse (Maschine)',
            'title': 'Alte Druckmaschine',
            'content': 'Die hydraulische Presse aus dem 19. Jahrhundert wird restauriert.',
            'expect_not': 'Medien'
        },
        {
            'name': 'Pressefreiheit (Medien)',
            'title': 'Pressefreiheit in Gefahr',
            'content': 'Die Presse warnt vor zunehmender Zensur und Einschränkungen.',
            'expect_has': 'Medien'
        },
    ]
    
    run_tests(tests)

def run_tests(tests):
    """Führt eine Liste von Tests aus"""
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\nTest: {test['name']}")
        title = test['title']
        content = test['content']
        tags = generate_tags(title, content)
        print(f"  Titel: {title}")
        print(f"  Tags: {tags}")
        
        success = True
        
        if 'expect_has' in test:
            if test['expect_has'] in tags:
                print(f"  ✓ Hat erwarteten Tag: {test['expect_has']}")
            else:
                print(f"  ✗ Fehlt erwarteter Tag: {test['expect_has']}")
                success = False
        
        if 'expect_not' in test:
            if test['expect_not'] not in tags:
                print(f"  ✓ Hat korrekterweise NICHT: {test['expect_not']}")
            else:
                print(f"  ✗ Hat fälschlicherweise: {test['expect_not']}")
                success = False
        
        if success:
            print("  ✓ PASS")
            passed += 1
        else:
            print("  ✗ FAIL")
            failed += 1
    
    print(f"\n{'=' * 80}")
    print(f"Ergebnis: {passed} bestanden, {failed} fehlgeschlagen")
    print(f"{'=' * 80}")

if __name__ == '__main__':
    print("=" * 80)
    print("UMFASSENDE KONTEXTBEZOGENE AUTO-TAGGING TESTS")
    print("=" * 80)
    
    test_gesundheit_context()
    test_wirtschaft_context()
    test_andere_kategorien()
    
    print("\n" + "=" * 80)
    print("ALLE TESTS ABGESCHLOSSEN!")
    print("=" * 80)
