import type { Locale, Localized } from "./types";

/**
 * MAJAL features and their real progress. Update `status` as stages are delivered:
 * the landing page and the dashboard both read this list.
 */
export type FeatureStatus = "available" | "in_development";
export type FeatureId =
  "diagnostic" | "commune" | "report" | "citizens" | "dataNeeds" | "assistant" | "presentation";

export type Feature = {
  id: FeatureId;
  status: FeatureStatus;
  stage: Localized;
  title: Localized;
  summary: Localized;
  points: Record<Locale, string[]>;
};

export const features: Feature[] = [
  {
    id: "diagnostic",
    status: "available",
    stage: { fr: "Étapes 1 et 2", ar: "المرحلتان 1 و2" },
    title: { fr: "Diagnostic territorial et carte", ar: "التشخيص الترابي والخريطة" },
    summary: {
      fr: "Une carte de chaque commune ou arrondissement, colorée selon l'indicateur choisi : équipements, accessibilité, cadre de vie, démographie.",
      ar: "خريطة لكل جماعة أو مقاطعة، ملوّنة حسب المؤشر المختار: التجهيزات، الولوجية، إطار العيش، الديموغرافيا.",
    },
    points: {
      fr: [
        "Indicateurs définis par l'urbaniste, modifiables sans programmation",
        "Source, date et niveau de fiabilité affichés pour chaque chiffre",
        "Fonctionne sans connexion internet",
      ],
      ar: [
        "مؤشرات يحددها المختص في التعمير، قابلة للتعديل دون برمجة",
        "المصدر والتاريخ ودرجة الموثوقية معروضة لكل رقم",
        "يشتغل دون اتصال بالإنترنت",
      ],
    },
  },
  {
    id: "commune",
    status: "available",
    stage: { fr: "Étape 2", ar: "المرحلة 2" },
    title: { fr: "Fiche commune et comparaison", ar: "بطاقة الجماعة والمقارنة" },
    summary: {
      fr: "Pour chaque commune : indicateurs clés, rang dans la province, écart à la moyenne et points d'attention.",
      ar: "لكل جماعة: المؤشرات الرئيسية، والترتيب داخل الإقليم، والفارق عن المتوسط، ونقاط الانتباه.",
    },
    points: {
      fr: [
        "Déficits signalés par une couleur et par un texte",
        "Jusqu'à quatre communes côte à côte",
        "Export en image et en tableau",
      ],
      ar: [
        "الخصاص مُبرز بلون وبنص معاً",
        "مقارنة ما يصل إلى أربع جماعات جنباً إلى جنب",
        "تصدير على شكل صورة وجدول",
      ],
    },
  },
  {
    id: "report",
    status: "available",
    stage: { fr: "Étape 3", ar: "المرحلة 3" },
    title: {
      fr: "Rapport rédigé par l'IA, vérifié",
      ar: "تقرير يحرره الذكاء الاصطناعي ويتم التحقق منه",
    },
    summary: {
      fr: "Un rapport de diagnostic rédigé en quelques minutes par une IA installée sur l'ordinateur, en français et en arabe ; export Word et PDF en français (en arabe à l'étape 7).",
      ar: "تقرير تشخيصي يُحرَّر في دقائق بذكاء اصطناعي مثبت على الحاسوب، بالفرنسية والعربية؛ التصدير بصيغتي Word وPDF بالفرنسية (وبالعربية في المرحلة 7).",
    },
    points: {
      fr: [
        "L'IA cite des faits identifiés : elle n'écrit jamais un chiffre elle-même",
        "Chaque nombre est contrôlé avant publication, ainsi que le sens des évolutions",
        "Mention « à valider par un urbaniste » jusqu'à sa validation",
      ],
      ar: [
        "يستشهد الذكاء الاصطناعي بوقائع محددة ولا يكتب أي رقم من تلقاء نفسه",
        "كل رقم يخضع للمراقبة قبل النشر، وكذلك اتجاه التطورات",
        "عبارة «في انتظار مصادقة مختص في التعمير» إلى حين المصادقة",
      ],
    },
  },
  {
    id: "citizens",
    status: "available",
    stage: { fr: "Étape 4", ar: "المرحلة 4" },
    title: { fr: "Écoute citoyenne", ar: "الإنصات للمواطنين" },
    summary: {
      fr: "Les contributions des habitants, en français, en arabe, en darija ou en amazighe, classées par thème et par lieu.",
      ar: "مساهمات السكان، بالفرنسية أو العربية أو الدارجة أو الأمازيغية، مصنفة حسب الموضوع والمكان.",
    },
    points: {
      fr: [
        "Anonymisation avant tout traitement",
        "Ce que disent les citoyens, mis en regard de ce que montrent les données",
        "L'outil propose, l'urbaniste valide : contributions « à vérifier »",
        "Contributions fictives dans le démonstrateur",
      ],
      ar: [
        "إخفاء الهوية قبل أي معالجة",
        "ما يقوله المواطنون في مقابل ما تُظهره المعطيات",
        "الأداة تقترح والمعمِّر يصادق: مساهمات «للتحقق»",
        "مساهمات افتراضية في النسخة التجريبية",
      ],
    },
  },
  {
    id: "dataNeeds",
    status: "available",
    stage: { fr: "Étape 5", ar: "المرحلة 5" },
    title: {
      fr: "Besoins en données et notes de demande",
      ar: "الحاجيات من المعطيات ومذكرات الطلب",
    },
    summary: {
      fr: "MAJAL montre ce qu'il pourrait calculer de plus avec les données de chaque institution, et prépare la demande.",
      ar: "يبيّن «مجال» ما يمكنه حسابه إضافةً بفضل معطيات كل مؤسسة، ويُعِدّ طلب الحصول عليها.",
    },
    points: {
      fr: [
        "Complétude des données, thème par thème",
        "Institution détentrice de chaque donnée manquante",
        "Simulateur : ce que chaque donnée permettrait de calculer, fiabiliser ou affiner",
        "Note de demande à relire et signer, en Word et en PDF",
      ],
      ar: [
        "مدى اكتمال المعطيات، موضوعاً بموضوع",
        "المؤسسة الحائزة لكل معطى ناقص",
        "محاكاة: ما يتيحه كل معطى من حساب أو تعزيز للموثوقية أو تدقيق",
        "مذكرة طلب للمراجعة والتوقيع، بصيغتي Word وPDF",
      ],
    },
  },
  {
    id: "assistant",
    status: "in_development",
    stage: { fr: "Après Tétouan", ar: "بعد تطوان" },
    title: { fr: "Assistant documentaire", ar: "المساعد الوثائقي" },
    summary: {
      fr: "Des questions posées aux documents d'urbanisme et aux textes publics, avec le document et la page cités.",
      ar: "أسئلة تُطرح على وثائق التعمير والنصوص العمومية، مع ذكر الوثيقة والصفحة.",
    },
    points: {
      fr: [
        "Réponses tirées uniquement des documents disponibles",
        "Citation du document et de la page",
        "Réponse indicative, à vérifier dans la source",
      ],
      ar: [
        "أجوبة مستخرجة من الوثائق المتوفرة فقط",
        "ذكر الوثيقة والصفحة",
        "جواب استرشادي، يجب التحقق منه في المصدر",
      ],
    },
  },
  {
    id: "presentation",
    status: "in_development",
    stage: { fr: "Étape 7", ar: "المرحلة 7" },
    title: { fr: "Mode présentation", ar: "وضع العرض" },
    summary: {
      fr: "Une démonstration fluide en plein écran, en moins de vingt minutes, même sans internet.",
      ar: "عرض سلس على كامل الشاشة، في أقل من عشرين دقيقة، حتى دون إنترنت.",
    },
    points: {
      fr: [
        "Navigation au clavier, étape par étape",
        "Bascule entre le français et l'arabe",
        "Bandeau « données fictives » quand c'est le cas",
      ],
      ar: [
        "تنقّل بلوحة المفاتيح، خطوة بخطوة",
        "التبديل بين الفرنسية والعربية",
        "شريط «معطيات افتراضية» كلما كان الأمر كذلك",
      ],
    },
  },
];
