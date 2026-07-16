# Phase 1 partial findings — bottle & cap plastic-type sorting (SO-101)

**Status:** deep-research workflow interrupted twice by usage limits. Search + claim-extraction 100% complete; adversarial verification ~15% complete (29/223 claims voted). Verdicts below are final (3-vote adversarial panel, >=2/3 refutes kill a claim).


**Research question:** How can a $55 SO-101 arm (LeRobot, ACT, 2x 640x480 RGB cams, no force sensing) pick and sort recyclable water bottles and caps by plastic type (PET vs HDPE vs PP) for easier downstream processing in Vietnam/HCMC — covering feasible plastic-ID techniques on cheap hardware, what transfers from commerc...


## Search angles covered

- ****: plastic type classification PET HDPE PP RGB camera deep learning low-cost NIR spectroscopy limitations black plastic recycling
- ****: AMP Robotics ZenRobotics TOMRA how robotic waste sorting works sensors AI vision suction gripper materials recovery facility
- ****: SO-101 SO-ARM100 LeRobot ACT policy pick and place sorting task vs YOLO object detection classifier grasp pipeline fine-tuning custom dataset
- ****: robot gripper grasping empty crushed plastic bottles deformable thin-walled objects small caps low payload two-finger gripper strategies
- ****: Vietnam ve chai scrap prices PET bottle HDPE PP cap price per kg VND informal recycling HCMC plastic value chain

## CONFIRMED claims (survived adversarial panel)

### C1. Even with the best of ten ML methods (PCA-CNN), the cheap 18-channel sensor only achieves 72.50% mean classification accuracy across the six plastic types — far below commercial NIR sorter performance, so it cannot be relied on as a sole discriminator.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Primary source (Sensors 2024, 24(9):2821; open-access via PMC11086069) confirms every specific in the claim. The sensor is the AS7265x SparkFun Triad, an 18-wavelength (410-940nm, vis-NIR) module costing ~£56 — matching "cheap 18-channel sensor." Six plastics were classified (PET, HDPE, PVC, LDPE, PP, PS). Ten ML methods were tested, and PCA-CNN was the best performer at exactly 72.50% mean accura
- Counter-source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11086069/

### C2. PET is the worst-recognized plastic (66% accuracy) with this low-cost sensor, and the largest confusions are exactly the pairs a bottle/cap sorter cares about: PET vs PVC and HDPE vs PP — meaning cheap NIR does not cleanly separate cap plastics (HDPE/PP) from each other.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Primary source verified via the PMC full text (PMC11086069) of Sensors 2024, 24(9), 2821 ("Low-Cost Recognition of Plastic Waste Using Deep Learning and a Multi-Spectral Near-Infrared Sensor"). Both factual assertions check out against exact text: (1) "accuracies ranging from a minimum of 66% for PET to the highest accuracy of 83.5% for PS" — PET is indeed the worst-recognized class; (2) "The larg
- Counter-source: https://onlinelibrary.wiley.com/doi/10.1002/mame.202500143 (selected-band NIR detection of post-consumer plastics) and SCiO Mini 740–1070 nm plastic ID studies — higher-cost "low-cost" sensors show better HDPE/PP separation, qualifying but not overturning the claim's generalization.

### C3. The review identifies limited real-world datasets, scalability issues, and environmental variability as the key challenges for AI-based plastic classification — directly relevant to deploying a hobby-scale sorter on messy Vietnamese ve chai streams rather than lab benches.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Verified: the source is a 2026 peer-reviewed review in Waste Management (Elsevier), "AI-based plastic waste classification for sorting purposes: A review on recent progresses and challenges" (PII S0956053X26002126). Direct fetch was 403-blocked, but web search independently surfaced the article by exact title and confirmed the abstract text: the review "identifies key challenges, including limited

### C4. Per the article's own caveat (surfaced in search-result text from the ScienceDirect page; not present in the Semantic Scholar abstract copy), reported high classification accuracies come from controlled conditions and restricted datasets, so published accuracy figures should be discounted when scoping a real-world build.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Independent web search confirms the exact sentence "Although high classification accuracies are reported, they are typically achieved under controlled conditions with restricted datasets that may not capture real-world complexities" belongs to ScienceDirect article S0956053X26002126 ("AI-based plastic waste classification for sorting purposes: A review on recent progresses and challenges", Waste M

### C5. The WaDaBa dataset used comprises 4,000 images of household plastic waste across 5 resin categories, collected over four months, with severe class imbalance (PET: 2,200 images vs Other: 40) — indicating a hobby-scale custom dataset (hundreds to low thousands of images) is in the right regime for this task.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): All factual elements verified against the primary source and the original dataset publication. The cited arXiv paper (2011.07747, "Application of Computer Vision Techniques for Segregation of Plastic Waste based on Resin Identification Code") states the WaDaBa database contains exactly 4,000 images in five resin categories with the per-class breakdown PET(01): 2,200, PE-HD(02): 600, PP(05): 640, P
- Counter-source: https://www.oaepublish.com/articles/ir.2021.15 (confirms 4000 images but reveals only ~100 unique objects at 40 photos each — a qualification, not a contradiction)

### C6. The 99%+ accuracies are likely optimistic for real deployment: the 80:10:10 split was done per-class on images, with no stated safeguard against the same physical object (photographed at multiple angles/lighting) appearing in both train and test sets, i.e., probable object-level data leakage.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Attempted refutation failed; the primary source confirms every element of the claim. Fetching https://ar5iv.labs.arxiv.org/html/2011.07747 verifies: (1) the paper reports 99%+ accuracies ("a high accuracy of 99.74%", "99.50% and 99.0% ... using Siamese and Triplet loss networks", "99.72% and 99.79%" for kNN); (2) the quoted split is real and image-level per class ("data is split in an 80:10:10 rat
- Counter-source: https://link.springer.com/chapter/10.1007/978-3-319-68720-9_8 (WaDaBa construction: 40 photos per object, ~100 objects — confirms rather than refutes)

### C7. The study's resin classes are ABS, HDPE, PS, and PVC from construction/demolition waste — it does NOT include PET or PP and does not test beverage bottles, so its results transfer only partially to the bottle/cap sorting task (HDPE is covered; the key PET-vs-PP-vs-HDPE cap distinction is not directly validated).

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Primary source confirmed via ADS abstract mirror (ScienceDirect returned 403 but search snippets of the article page corroborate): the paper "Deep learning-based construction and demolition plastic waste classification by resin type using RGB images" (Resources, Conservation & Recycling 2025, DOI 10.1016/j.resconrec.2024.107937) states "The dataset comprises four commonly used plastic types in con
- Counter-source: https://ui.adsabs.harvard.edu/abs/2025RCR...21207937R/abstract

### C8. Black polymers are traditionally undetectable by standard optical sorting sensors (NIR-based), and TOMRA requires optional add-on technologies beyond its base AUTOSORT sensor configuration to identify them — confirming that dark/black plastics defeat conventional NIR sorting.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Quote verified verbatim on the primary TOMRA AUTOSORT page ("Optional add-on technologies expand material identification capabilities for traditionally undetectable fractions like black polymers"), and the underlying physics is independently corroborated: a peer-reviewed study (PMC6418689) states carbon black absorbs NIR light making optical identification impossible in the standard 0.9-1.7 um ran

### C9. AMP Robotics' commercial sorting AI (Neuron platform) identifies recyclables using visual features from cameras — colors, textures, shapes, sizes, patterns, and brand labels — rather than NIR spectroscopy, meaning RGB-camera-based classification is the core sensing modality used by a leading commercial robotic sorter and is in principle the same modality available on a cheap 640x480-camera hobby arm.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): The claim survives adversarial checks. (1) The quoted milestone article supports the visual-features part verbatim ("recognizing different colors, textures, shapes, sizes, patterns, and even brand labels"). (2) The stronger "rather than NIR" part, which the original quote alone would not support, is independently confirmed by AMP's own current technology page (ampsortation.com/technologies/vision)
- Counter-source: https://www.energy.gov/sites/prod/files/2020/07/f77/2203-1827_AMP_Robotics_Corp_Topic_2_Waste_t_Summary.pdf (2020 DOE R&D project exploring NIR/XRF/Raman sensor fusion — research effort, not the deployed RGB-camera product)

### C10. ACT trained via imitation learning (100 teleoperated demos per task) on the SO-101 achieved 75% success on simple pick-and-place (Pen Transfer) but 0% success on the selective sorting task requiring object identification among distractors (Selective Color Sorting), directly showing that end-to-end ACT fails at the identify-then-sort structure the bottle/cap task requires.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): All factual assertions verified directly against the primary source (arXiv:2606.08881, "Benchmarking Vision-Language-Action Models on SO-101: Failure and Recovery Analysis," June 2026). Fetched the HTML full text: Table 3 reports ACT at exactly 75% on Pen Transfer and 0% on Selective Color Sorting (also 10% Multi-Object Packing, 50% Precision Pen Placement); the paper states verbatim "For each tas
- Counter-source: https://arxiv.org/html/2606.08881v2 (same paper, Table 3: SmolVLA 5%, Wall-X 0%, pi-0.5 10% on Selective Color Sorting — failure is universal across policies, not ACT-specific)

### C11. Even with the best-performing method (CNN with PCA preprocessing), the low-cost sensor achieved only 72.50% overall accuracy classifying six plastic types (PET, HDPE, PVC, LDPE, PP, PS), with an MLP reaching 70.25% — well below the reliability needed for autonomous value-adding sorting.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Verified against the open-access full text (PMC11086069, identical to MDPI Sensors 2024, 24(9), 2821; mdpi.com returned 403). The paper tests a ~GBP 56 SparkFun AS7265x Triad multi-spectral sensor (410-940 nm, 18 channels) on six plastics (PET, HDPE, PVC, LDPE, PP, PS). PCA-CNN is confirmed as the best method at exactly 72.50% overall accuracy; PCA-MLP at exactly 70.25%. The supporting quote appea
- Counter-source: https://animorepository.dlsu.edu.ph/conf_shsrescon/2025/paper_csr/12/

### C12. PET was the single worst-recognized plastic type at 66% accuracy — directly problematic for the bottle-sorting use case, since PET bottles are the primary target stream and would be misclassified roughly one time in three by this cheap-sensor approach.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Primary source verified via PMC full text (PMC11086069, Sensors 2024, 24(9):2821). The paper's best configuration (PCA-CNN, 72.5% mean accuracy) reports per-class confusion-matrix accuracies "ranging from a minimum of 66% for PET to the highest accuracy of 83.5% for PS" — PET was the single worst-recognized class in that configuration and also the worst (60%) in the raw-CNN configuration. The sens
- Counter-source: https://animorepository.dlsu.edu.ph/conf_shsrescon/2025/paper_csr/12/ (DLSU SHS conference, 92% overall with AS7265x — low-quality, not PET-specific, does not overturn)

### C13. The dominant AI approaches for plastic waste classification in the 2015-2025 literature are CNNs, YOLO object-detection architectures, and Transformer-based models, often integrated with spectroscopic sensing (NIR, FTIR, Raman) rather than RGB vision alone — directly relevant to whether a 2x RGB-camera SO-101 setup can identify resin type without spectroscopy.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Claim survives adversarial checks. (1) Source verified as genuine and high-quality: "AI-based plastic waste classification for sorting purposes: A review on recent progresses and challenges" is a PRISMA-guided systematic review in Waste Management (Elsevier, 2026) covering exactly 112 articles from 2015-2025 — matching the claim's stated literature window. The supporting quote matches the publishe
- Counter-source: https://arxiv.org/html/2505.16513v1 (checked as potential contradiction; instead corroborates that RGB-only vision underperforms for resin-type identification)

### C14. The field's key unsolved challenges for deployable plastic sorting are limited real-world datasets, scalability issues, and environmental variability — meaning a hobby-arm CV classifier trained on custom bottle/cap data will face a documented domain-gap problem between lab/benchmark datasets and real waste streams.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): The claim survives adversarial checking. (1) Source verification: the PII S0956053X26002126 resolves to "AI-based plastic waste classification for sorting purposes: A review on recent progresses and challenges," a 2026 peer-reviewed review in a ScienceDirect journal (Waste Management); direct fetch was 403-blocked, but web search independently confirms both the article and the exact quoted languag
- Counter-source: https://arxiv.org/html/2505.16513v1

### C15. Accurate resin-type classification can be compressed onto edge-deployable hardware: the authors used knowledge distillation from a large Swin Transformer teacher into a lightweight MobileNetV3 student designed for edge devices, meaning a cheap single-board computer or laptop could run the classifier for a hobby sorting arm.

- Votes: 3 (1 refute)
- Evidence (one voter, abridged): The claim's factual core is confirmed. The paper (Resources, Conservation & Recycling, S0921344924005305, 2024/2025 — peer-reviewed journal, primary source) does exactly what the quote says: it trains large models (ResNet, ResNeXt, RegNet, Swin Transformer) via ImageNet transfer learning, then applies knowledge distillation using the Swin Transformer's output class probabilities to boost the accur
- Counter-source: https://ui.adsabs.harvard.edu/abs/2025RCR...21207937R/abstract (abstract confirms method but shows dataset is ABS/HDPE/PS/PVC C&D plastics, not PET/PP bottles; no confirmed on-device latency benchmark)

### C16. Black plastics are hard to identify with NIR spectroscopy because carbon black absorbs NIR light, giving low reflectance and near-featureless spectra — the core physical limit relevant to any cheap NIR sensor add-on for dark bottle caps.

- Votes: 3 (0 refute)
- Evidence (one voter, abridged): Claim survives adversarial review. (1) The quote from the peer-reviewed 2025 Measurement (Elsevier) paper directly supports it, and the paper's own title calls black-plastic NIR spectra "featureless"; the claim's "hard to identify" is weaker than the source's "unidentifiable," so no overreach. (2) Independent corroboration: PMC6418689 (MIR photon up-conversion paper: "fails when NIR light is fully
- Counter-source: https://pmc.ncbi.nlm.nih.gov/articles/PMC6418689/ (corroborating, not contradicting); workaround sources: https://www.sciencedirect.com/science/article/pii/S0956053X25005860 (MWIR alternative), https://packagingeurope.com/news/greif-launches-nir-detectable-black-plastic-screw-cap/8234.article (carbon-black-free colorants)

### C17. Even under controlled lab conditions with hyperspectral NIR imaging, machine learning classifiers on black plastics achieved only modest accuracy: XGBoost 72.50%, PLS-DA 51.21%, and CNN 69.63%.

- Votes: 2 (0 refute)
- Evidence (one voter, abridged): Claim verified against the primary source: "Spectral preprocessing across featureless NIR and feature-rich MIR: Machine learning classification of black plastics," Measurement (2025), DOI 10.1016/j.measurement.2025.119480. Independent search confirms the exact figures — XGBoost 72.50%, PLS-DA 51.21%, CNN 69.63% — for NIR hyperspectral imaging of black plastics under controlled laboratory condition
- Counter-source: https://www.specim.com/overcoming-black-plastic-recycling-challenge-with-mwir-hyperspectral-imaging-technology/ (MWIR HSI achieves strong black-plastic identification — different wavelength band, qualifies rather than contradicts the NIR claim)


## REFUTED claims (do NOT rely on these)

### R1. A ~GBP 56 (~USD 70) SparkFun Triad Spectroscopy Sensor (AS7265x, 18 channels spanning 410-940 nm visible-to-NIR) can classify six household plastic types (PET, HDPE, PVC, LDPE, PP, PS), making spectroscopy-based plastic ID a plausible cheap sensor add-on for a hobby-budget sorter.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The claim overreaches on multiple axes. (1) The supporting quote only establishes the sensor's COST (~GBP 56), not classification capability. (2) The paper itself (Sensors, Apr 2024, PMC11086069) reports only 72.5% mean accuracy at best (PCA-CNN), with PET — the single most important class for a Vietnam bottle-sorting application — the WORST class at 66%, systematically confused with PVC; HDPE con
- Counter-source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11086069/ (full text of the cited paper: 72.5% best accuracy, PET worst at 66%, sealed-box setup, 8 PVC items); https://www.nature.com/articles/s41598-023-49765-z (Vis-NIR fails on black plastics)

### R2. The current state of the art in plastic waste classification pairs deep-learning vision models (CNNs, YOLO architectures, Transformers) with spectroscopic sensing (NIR, FTIR, Raman) — i.e., pure RGB vision is routinely augmented by spectroscopy in the literature, not used alone.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The claim overreaches its supporting quote in two ways. (1) The quote is a review's scope statement — it says the review "assesses their integration with" NIR/FTIR/Raman spectroscopy. Assessing integration is not evidence that RGB vision is "routinely augmented by spectroscopy ... not used alone"; a review covering both modalities says nothing about the prevalence of pure-RGB pipelines. (2) The "n
- Counter-source: https://arxiv.org/pdf/2412.20232 (WaDaBa RGB-only plastic classification); https://link.springer.com/article/10.1007/s00521-024-10855-2 (RGB YOLO waste detection); https://www.sciencedirect.com/science/article/pii/S0950705125000760 (RGB-only automated waste classification)

### R3. The review's recommended future directions are lightweight models, multi-sensor fusion, and edge-AI deployment — supporting the feasibility premise that low-cost edge hardware (like an SO-101 with cheap cams plus auxiliary sensors) is where the field is heading.

- Votes: 3 (2 refute)
- Evidence (one voter, abridged): The quote is authentic (verified against the ScienceDirect/ResearchGate abstract of the 2026 Waste Management review), but the claim inverts its meaning. A review's "future research directions" section identifies UNSOLVED gaps — the paper is saying lightweight models, multi-sensor fusion, and edge-AI deployment are areas needing work, not that low-cost edge hardware is currently feasible for polym
- Counter-source: https://www.researchgate.net/publication/403962852_AI-based_plastic_waste_classification_for_sorting_purposes_A_review_on_recent_progresses_and_challenges (the review's own challenges section: visually similar plastics require spectroscopic sensing; real-world datasets, contamination, and real-time edge deployment remain open problems)

### R4. A Siamese network with only 4 convolutional layers, trained on RGB images resized to 105x105, achieved ~99.7% accuracy classifying household plastic waste into 5 resin-code categories (PET, PE-HD, PP, PS, Other) on the WaDaBa dataset — suggesting resin-code-level classification from plain RGB is achievable with very lightweight models suitable for cheap hardware.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The accuracy figure is real but the generalization inference is invalid due to train/test leakage. WaDaBa's 4,000 images derive from only ~100 unique physical objects: per the dataset authors (Bobulski & Piatkowski 2018), each object was photographed 40 times (10 rotation angles x 2 light sources x multiple deformation levels), yielding 40 near-duplicate images per object. The paper (arXiv 2011.07
- Counter-source: https://www.researchgate.net/publication/320085365_PET_Waste_Classification_Method_and_Plastic_Waste_DataBase_-_WaDaBa (dataset construction: 40 photos per object, ~100 objects); arXiv 2011.07747 itself (image-level 80:10:10 split, no per-object separation)

### R5. Peer-reviewed research demonstrates that deep learning on plain RGB images (no NIR/hyperspectral hardware) can classify rigid plastic waste by resin type, and the authors conclude RGB is a practical low-cost alternative to costly spectroscopic identification systems — directly supporting the feasibility of camera-only plastic-type ID on a $55 arm's 640x480 webcams.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The source and quote are genuine, but the claim overreaches on the load-bearing clause. The paper (Resources, Conservation and Recycling, Vol 212, 107937, 2025) classified CONSTRUCTION & DEMOLITION plastic waste across exactly four resins: ABS, HDPE, PS, and PVC. It never tested PET or PP — the two resins that dominate the actual research question (PET water bottles vs HDPE/PP caps) — nor clear/tr
- Counter-source: https://ui.adsabs.harvard.edu/abs/2025RCR...21207937R/abstract (confirms resin set is ABS/HDPE/PS/PVC C&D waste, no PET/PP, no beverage containers, no low-res webcam testing)

### R6. A low-cost multispectral sensor module based on the OSRAM AS7265x chipset (~GBP 75 for the module, ~GBP 15 for the chipset alone) provides 18 spectral channels from 410 nm to 940 nm, versus GBP 6k-50k for traditional NIR spectrometers — meaning affordable 'NIR' options for a $55-arm project only cover the visible/very-near-IR band, not the 1000-1700 nm region commercial plastic sorters use.

- Votes: 3 (2 refute)
- Evidence (one voter, abridged): The factual core of the claim checks out: ams-OSRAM's own product page confirms the AS7265x is an 18-channel chipset covering 410-940nm (FWHM 20nm), matching the supporting quote. However, the claim's concluding inference — that affordable 'NIR' options for a hobby project "only cover the visible/very-near-IR band, not the 1000-1700 nm region" — is an overreach beyond the quoted source and is dire
- Counter-source: https://docs.plasticscanner.com/how_it_works (LED array 855-1650nm, InGaAs photodiode); https://hackaday.com/2021/12/13/an-open-source-detector-for-identifying-plastics/; https://onlinelibrary.wiley.com/doi/10.1002/mame.202500143

### R7. RGB-image-only classification of plastic waste into resin code categories (PET, PE-HD, PP, PS, Other) is achievable with ~99.7% accuracy using a small Siamese/triplet CNN with KNN, on the WaDaBa benchmark — supporting the feasibility of camera-only plastic-type ID on cheap hardware without NIR spectroscopy.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The 99.72%/99.79% figures are real (arXiv 2011.07747 reports them), but they do not support the claim's conclusion, for a fatal methodological reason: WaDaBa's ~4,000 images are derived from only ~100 unique physical objects, each photographed ~40 times under different rotations and lighting (per the original dataset paper, Bobulski & Piatkowski 2017, Springer 978-3-319-68720-9_8: "a minimum of 10
- Counter-source: https://link.springer.com/chapter/10.1007/978-3-319-68720-9_8 (WaDaBa dataset paper: ~100 objects x 40 images each, implying object-level train/test leakage under random image splits)

### R8. The method classifies plastic type from the whole object's visual appearance, not by reading the molded resin-code triangle symbol — i.e., a vision model can infer resin type from bottle shape/texture/color priors alone.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The first half of the claim is technically accurate but the "i.e." generalization is an overreach the source cannot support. (1) Method check: arXiv 2011.07747 does feed whole-object WaDaBa images to a Siamese/Triplet-loss classifier with no symbol-reading step, so "classifies from whole-object appearance" describes the pipeline correctly. (2) But the inference "a vision model can infer resin type
- Counter-source: https://meyer-corp.eu/article/how-optical-sorters-separates-pet-from-pvc-tackling-plastic-cross-contamination/ (RGB cannot distinguish polymer types; NIR required) and https://qualitastech.com/app-notes/nir-swir-spectral-imaging-automatic-polymer-identification/ (polymer signal lies outside visible 380-700nm range)

### R9. One-shot/few-shot metric learning (Siamese/triplet networks) makes high accuracy possible with only 4,000 images and no augmentation, because pairwise training generates n-squared instances — relevant to a hobbyist who can only collect a small custom bottle/cap dataset.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The claim overreaches from a leaky benchmark. The source paper (arXiv 2011.07747) does report 99.5-99.74% with Siamese/Triplet networks on WaDaBa "without augmentation," but the dataset structure invalidates the generalization the claim depends on: WaDaBa's 4,000 images come from only ~100 unique physical objects, each photographed 40 times (2 lighting types x 10 rotation angles, plus 3 damage lev
- Counter-source: https://www.researchgate.net/publication/320085365_PET_Waste_Classification_Method_and_Plastic_Waste_DataBase_-_WaDaBa (WaDaBa: 40 photos per object, ~100 objects); https://pmc.ncbi.nlm.nih.gov/articles/PMC7148474/ (Siamese nets on small datasets still need augmentation/regularization)

### R10. Standard RGB camera images, processed with deep learning, are presented as a viable low-cost alternative to expensive sensing systems (e.g., NIR/hyperspectral) for identifying plastics by resin type — directly supporting the feasibility of resin-type classification with the SO-101's 640x480 RGB cameras.

- Votes: 3 (3 refute)
- Evidence (one voter, abridged): The claim overreaches the source in two ways. (1) Scope mismatch: the cited paper (S0921344924005305, Resources Conservation & Recycling) studies construction-and-demolition plastic waste across four resins — ABS, HDPE, PS, PVC — not the PET/HDPE/PP bottle-and-cap distinction the research question needs; it never tests PET vs PP, the hardest pair for the SO-101 task (clear PET bottle vs clear/whit
- Counter-source: https://arxiv.org/html/2505.16513v1 (Detailed Evaluation of Modern Machine Learning Approaches for Optic Plastics Sorting, 2025); https://doi.org/10.3390/jimaging12060267 (hyperspectral vs RGB on transparent/white plastics)


## Incomplete verifications (1 vote in, needs 2 more each)

- (1 vote, refutes=0) Selective sorting (pick the correct object among distractors) was the hardest benchmark task on SO-101 for every evaluated policy, with all methods — ACT, SmolVLA, Wall-X, and pi-0.5 — scoring only 0-10% success, versus 70-95% for plain pick-and-place transfer.
- (1 vote, refutes=0) On real-world black plastics (from waste electrical and electronic equipment), NIR-trained models collapsed to under 10% accuracy — i.e., lab NIR results do not transfer to field waste streams.

## Unverified claims

194 extracted claims never reached the verification stage — full list with sources/quotes in `salvage_unverified_claims.json`. All 223 claims + full vote details in `salvage_claims.json`.
