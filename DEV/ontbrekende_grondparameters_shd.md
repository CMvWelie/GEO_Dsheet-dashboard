# Ontbrekende grondparameters uit `.shd`

Deze notitie beschrijft de grondvelden die in de voorbeeldbestanden onder
`DKIB_geotechniek/03 AI-automatisering/Testfiles` in `[SOIL]`-blokken staan,
maar nog niet als losse velden in `parsers.models.Soil` en de debug-invoer
worden getoond.

## Reeds beschikbaar in parser en debug-invoer

| `.shd` veld | Debug-kolom | Betekenis |
|---|---|---|
| `SoilColor` | `kleur` | Grondkleur uit D-Sheet |
| `SoilGamDry` | `gamma_d` | Droog volumegewicht |
| `SoilGamWet` | `gamma_n` | Nat/verzadigd volumegewicht |
| `SoilCohesion` | `c'` | Cohesie |
| `SoilPhi` | `phi` | Hoek van inwendige wrijving |
| `SoilDelta` | `delta` | Wandwrijvingshoek |
| `SoilLa` | `Ka` | Actieve gronddrukcoefficient |
| `SoilLn` | `Kn` | Neutrale gronddrukcoefficient |
| `SoilLp` | `Kp` | Passieve gronddrukcoefficient |
| `SoilOCR` | `OCR` | Overconsolidatieratio |
| `SoilShellFactor` | `shell factor` | Shell factor |
| `SoilCurKo1` | `kh1` | Horizontale beddingconstante curve 1 |
| `SoilCurKo2` | `kh2` | Horizontale beddingconstante curve 2 |
| `SoilCurKo3` | `kh3` | Horizontale beddingconstante curve 3 |

## Nog ontbrekend in parser en debug-invoer

| `.shd` veld | Categorie | Omschrijving / aandachtspunt |
|---|---|---|
| `SoilSoilType` | Classificatie | D-Sheet grondtype-code. Betekenis van codes nog mappen naar labels. |
| `SoilGrainType` | Classificatie | Korreltype-code. Betekenis van codes nog mappen naar labels. |
| `SoilRelativeDensity` | Grondeigenschap | Relatieve dichtheid. Vooral relevant voor zandige gronden. |
| `SoilEModMenard` | Stijfheid | Menard E-modulus. Alleen inhoudelijk gebruiken in combinatie met `SoilUseMenard`. |
| `SoilPermeabKx` | Doorlatendheid | Horizontale doorlatendheid. Eenheid/interpretatie controleren tegen D-Sheet export. |
| `SoilStdCohesion` | Statistiek | Standaardafwijking cohesie. |
| `SoilStdPhi` | Statistiek | Standaardafwijking wrijvingshoek. |
| `SoilDistCohesion` | Statistiek | Verdelingscode voor cohesie. Betekenis van codes nog mappen. |
| `SoilDistPhi` | Statistiek | Verdelingscode voor wrijvingshoek. Betekenis van codes nog mappen. |
| `SoilIsDeltaAngleAutomaticallyCalculated` | Instelling | Geeft aan of `SoilDelta` automatisch berekend is. |
| `SoilUseMenard` | Instelling | Schakelaar voor Menard-model. |
| `SoilUseBrinchHansen` | Instelling | Schakelaar voor Brinch-Hansen-model. |
| `SoilLambdaType` | Lambda-instelling | Type-code voor lambda-bepaling. Betekenis van codes nog mappen. |
| `SoilLam1` | Lambda-parameter | Lambda-waarde 1. |
| `SoilLam2` | Lambda-parameter | Lambda-waarde 2. |
| `SoilLam3` | Lambda-parameter | Lambda-waarde 3. |
| `SoilKb0` | Bedding / veerdata | Kb basiswaarde 0. Interpretatie controleren tegen D-Sheet documentatie. |
| `SoilKb1` | Bedding / veerdata | Kb basiswaarde 1. |
| `SoilKb2` | Bedding / veerdata | Kb basiswaarde 2. |
| `SoilKb3` | Bedding / veerdata | Kb basiswaarde 3. |
| `SoilKb4` | Bedding / veerdata | Kb basiswaarde 4. |
| `SoilKo0` | Bedding / veerdata | Ko basiswaarde 0. Interpretatie controleren tegen D-Sheet documentatie. |
| `SoilKo1` | Bedding / veerdata | Ko basiswaarde 1. |
| `SoilKo2` | Bedding / veerdata | Ko basiswaarde 2. |
| `SoilKo3` | Bedding / veerdata | Ko basiswaarde 3. |
| `SoilKo4` | Bedding / veerdata | Ko basiswaarde 4. |
| `SoilCurKb1` | Bedding / veerdata | Kb curvewaarde 1. Tegenhanger van de reeds getoonde `SoilCurKo1`. |
| `SoilCurKb2` | Bedding / veerdata | Kb curvewaarde 2. |
| `SoilCurKb3` | Bedding / veerdata | Kb curvewaarde 3. |
| `SoilHorizontalBehaviourType` | Modelinstelling | Code voor horizontaal grondgedrag. Betekenis van codes nog mappen. |
| `SoilElasticity` | Stijfheid | Elasticiteitswaarde. |
| `SoilDefaultElasticity` | Instelling | Geeft aan of standaardelasticiteit wordt gebruikt. |

## Implementatieadvies

Voor debug-doeleinden is de veiligste aanpak om deze velden eerst als ruwe
waarden aan `Soil` toe te voegen met namen die dicht bij de `.shd` liggen. Voor
rapportage of berekeningen moeten codevelden eerst expliciet naar betekenisvolle
labels worden vertaald, zodat numerieke D-Sheet-keuzecodes niet per ongeluk als
fysische parameters worden gelezen.
