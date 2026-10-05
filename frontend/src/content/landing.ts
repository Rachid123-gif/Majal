import type { Locale } from "./types";

/**
 * Texts of the public landing page.
 * Every figure comes from the MAJAL opportunity study (October 2026) and keeps its source.
 * Arabic texts are provisional translations, to be reviewed by the scientific referent.
 */
export type KeyFigure = { value: number; unit: string; detail: string; source: string };
export type Card = { title: string; text: string };

export type LandingContent = {
  nav: { project: string; features: string; territories: string; guarantees: string };
  login: string;
  menu: string;
  close: string;
  hero: {
    eyebrow: string;
    title: string;
    subtitle: string;
    discover: string;
    mapLabel: string;
    cities: { rabat: string; tetouan: string };
  };
  stakes: { eyebrow: string; title: string; intro: string; figures: KeyFigure[]; note: string };
  problem: {
    eyebrow: string;
    title: string;
    before: { title: string; items: string[] };
    after: { title: string; items: string[] };
  };
  featuresSection: {
    eyebrow: string;
    title: string;
    intro: string;
    inDevelopment: string;
    available: string;
    mockup: string;
  };
  territories: {
    eyebrow: string;
    title: string;
    intro: string;
    unitsLabel: string;
    themesLabel: string;
    items: {
      code: "rabat" | "tetouan";
      name: string;
      kind: string;
      region: string;
      units: string;
      themes: string[];
    }[];
  };
  how: { eyebrow: string; title: string; steps: Card[]; motto: string };
  guarantees: { eyebrow: string; title: string; items: Card[] };
  project: {
    eyebrow: string;
    title: string;
    text: string;
    role: string;
    affiliation: string;
    photo: string;
    contact: string;
    contactPending: string;
  };
  footer: { demo: string; legal: string; map: string; rights: string; tagline: string };
};

const STUDY_FR = "étude d'opportunité MAJAL (octobre 2026)";
const STUDY_AR = "دراسة الجدوى لمشروع «مجال» (أكتوبر 2026)";

export const landing: Record<Locale, LandingContent> = {
  fr: {
    nav: {
      project: "Le projet",
      features: "Fonctionnalités",
      territories: "Territoires",
      guarantees: "Garanties",
    },
    login: "Se connecter",
    menu: "Menu",
    close: "Fermer",
    hero: {
      eyebrow: "Démonstrateur · Rabat et Tétouan",
      title: "Le copilote IA de l'intelligence territoriale",
      subtitle:
        "Des données publiques dispersées aux diagnostics territoriaux, en quelques minutes.",
      discover: "Découvrir",
      mapLabel: "Carte du Maroc situant Rabat et Tétouan, les deux territoires de démonstration",
      cities: { rabat: "Rabat", tetouan: "Tétouan" },
    },
    stakes: {
      eyebrow: "L'enjeu",
      title: "Une nouvelle génération de programmes territoriaux",
      intro:
        "Les programmes de développement territorial intégré reposent sur des diagnostics territoriaux et des concertations citoyennes dans chaque province.",
      figures: [
        {
          value: 210,
          unit: "milliards de dirhams",
          detail: "pour les programmes de développement territorial intégré",
          source: "Conseil des ministres du 9 avril 2026 (Le Desk)",
        },
        {
          value: 8,
          unit: "ans",
          detail: "durée de ces programmes",
          source: "Conseil des ministres du 9 avril 2026 (Le Desk)",
        },
        {
          value: 75,
          unit: "provinces et préfectures",
          detail: "concernées par les diagnostics et les concertations citoyennes",
          source: "FNH : concertations dans les 75 provinces",
        },
        {
          value: 12,
          unit: "régions",
          detail: "un institut Jazari par région, selon la stratégie Maroc IA 2030",
          source: "Infomédiaire : Maroc IA 2030, instituts Jazari",
        },
      ],
      note: `Chiffres repris de l'${STUDY_FR}, qui cite ces sources.`,
    },
    problem: {
      eyebrow: "Le problème, la solution",
      title: "La donnée territoriale existe. Il manque l'outil qui la transforme en décision.",
      before: {
        title: "Aujourd'hui",
        items: [
          "Des études ponctuelles, longues et coûteuses",
          "Des données dispersées entre de nombreux acteurs",
          "Des rapports vite dépassés",
          "Une parole citoyenne difficile à exploiter",
        ],
      },
      after: {
        title: "Avec MAJAL",
        items: [
          "Un diagnostic chiffré, actualisable à tout moment",
          "Les sources publiques réunies dans un seul outil",
          "Un rapport rédigé en quelques minutes, validé par un urbaniste",
          "Les contributions citoyennes classées par thème et par lieu",
        ],
      },
    },
    featuresSection: {
      eyebrow: "Fonctionnalités",
      title: "Sept outils au service du diagnostic territorial",
      intro:
        "Le démonstrateur est en cours de construction. Chaque fonctionnalité indique honnêtement son état d'avancement.",
      inDevelopment: "En cours de développement",
      available: "Disponible",
      mockup: "Maquette d'illustration — aucune donnée réelle",
    },
    territories: {
      eyebrow: "Deux territoires, un seul outil",
      title: "Une capitale urbaine, une province entre ville et campagne",
      intro:
        "Le même outil s'adapte à des réalités très différentes sans changer une ligne de code : seule la configuration change.",
      unitsLabel: "Unités d'analyse",
      themesLabel: "Enjeux suivis",
      items: [
        {
          code: "rabat",
          name: "Rabat",
          kind: "Capitale entièrement urbaine",
          region: "Région Rabat-Salé-Kénitra",
          units: "Arrondissements et communes de l'agglomération Rabat-Salé-Skhirate-Témara",
          themes: ["Accès au tramway et au bus", "Espaces verts", "Équipements de proximité"],
        },
        {
          code: "tetouan",
          name: "Tétouan",
          kind: "Province urbaine et rurale, entre littoral et montagne",
          region: "Région Tanger-Tétouan-Al Hoceïma",
          units: "Communes urbaines et rurales, douars",
          themes: ["Routes revêtues et pistes", "Eau potable et électricité", "Transport scolaire"],
        },
      ],
    },
    how: {
      eyebrow: "Comment ça marche",
      title: "Des données à la décision, en trois temps",
      steps: [
        {
          title: "Données",
          text: "Recensement, OpenStreetMap, imagerie satellite, documents d'urbanisme, contributions citoyennes.",
        },
        {
          title: "Intelligence artificielle",
          text: "Calcule les indicateurs, compare les communes, synthétise la parole citoyenne et rédige le rapport.",
        },
        {
          title: "Décision",
          text: "L'urbaniste relit et valide. Le décideur arbitre.",
        },
      ],
      motto: "L'outil propose, l'urbaniste valide.",
    },
    guarantees: {
      eyebrow: "Nos garanties",
      title: "Un outil digne de confiance",
      items: [
        {
          title: "Chaque chiffre est sourcé",
          text: "Source, date et niveau de fiabilité sont affichés : officiel, ouvert, estimé ou fictif.",
        },
        {
          title: "L'IA n'invente aucun chiffre",
          text: "Elle cite des faits vérifiés. Un nombre dont l'origine n'est pas tracée bloque le rapport.",
        },
        {
          title: "Données personnelles protégées",
          text: "Anonymisation systématique avant tout traitement, dans le respect de la loi 09-08.",
        },
        {
          title: "Une IA souveraine possible",
          text: "MAJAL peut fonctionner avec un modèle hébergé au Maroc, sans aucun service étranger.",
        },
      ],
    },
    project: {
      eyebrow: "Le projet",
      title: "Une démarche scientifique",
      text: "MAJAL est conçu sous la direction scientifique d'un Professeur Habilité de l'École Nationale d'Architecture de Tétouan, spécialiste en urbanisme, gouvernance urbaine, intelligence territoriale et marketing territorial.",
      role: "Référent scientifique",
      affiliation: "Professeur Habilité, École Nationale d'Architecture de Tétouan",
      photo: "[Photo]",
      contact: "Nous contacter",
      contactPending: "Adresse de contact à compléter",
    },
    footer: {
      demo: "Démonstrateur — données de démonstration",
      legal: "Mentions légales : [à compléter]",
      map: "Fond de carte : Natural Earth (domaine public)",
      rights: "© 2026 MAJAL",
      tagline: "Copilote d'intelligence territoriale",
    },
  },
  ar: {
    nav: {
      project: "المشروع",
      features: "الوظائف",
      territories: "المجالات الترابية",
      guarantees: "الضمانات",
    },
    login: "تسجيل الدخول",
    menu: "القائمة",
    close: "إغلاق",
    hero: {
      eyebrow: "نسخة تجريبية · الرباط وتطوان",
      title: "المساعد الذكي للذكاء الترابي",
      subtitle: "من المعطيات العمومية المتفرقة إلى التشخيصات الترابية، في دقائق معدودة.",
      discover: "اكتشف",
      mapLabel: "خريطة المغرب تبيّن موقع الرباط وتطوان، المجالين الترابيين للعرض التجريبي",
      cities: { rabat: "الرباط", tetouan: "تطوان" },
    },
    stakes: {
      eyebrow: "الرهان",
      title: "جيل جديد من البرامج الترابية",
      intro:
        "تقوم برامج التنمية الترابية المندمجة على تشخيصات ترابية ومشاورات مع المواطنين في كل إقليم.",
      figures: [
        {
          value: 210,
          unit: "مليار درهم",
          detail: "لبرامج التنمية الترابية المندمجة",
          source: "مجلس الوزراء بتاريخ 9 أبريل 2026 (Le Desk)",
        },
        {
          value: 8,
          unit: "سنوات",
          detail: "مدة هذه البرامج",
          source: "مجلس الوزراء بتاريخ 9 أبريل 2026 (Le Desk)",
        },
        {
          value: 75,
          unit: "إقليماً وعمالة",
          detail: "معنية بالتشخيصات والمشاورات مع المواطنين",
          source: "FNH : المشاورات في الأقاليم الـ75",
        },
        {
          value: 12,
          unit: "جهة",
          detail: "معهد «الجزري» في كل جهة، حسب استراتيجية «Maroc IA 2030»",
          source: "Infomédiaire : Maroc IA 2030، معاهد الجزري",
        },
      ],
      note: `أرقام مأخوذة من ${STUDY_AR}، التي تستند إلى هذه المصادر.`,
    },
    problem: {
      eyebrow: "المشكلة والحل",
      title: "المعطيات الترابية موجودة. ما ينقص هو الأداة التي تحوّلها إلى قرار.",
      before: {
        title: "اليوم",
        items: [
          "دراسات ظرفية، طويلة ومكلفة",
          "معطيات متفرقة بين فاعلين كثيرين",
          "تقارير سرعان ما تتجاوزها الأحداث",
          "صوت المواطنين يصعب استثماره",
        ],
      },
      after: {
        title: "مع «مجال»",
        items: [
          "تشخيص مرقّم قابل للتحيين في أي وقت",
          "المصادر العمومية مجتمعة في أداة واحدة",
          "تقرير يُحرَّر في دقائق ويصادق عليه مختص في التعمير",
          "مساهمات المواطنين مصنفة حسب الموضوع والمكان",
        ],
      },
    },
    featuresSection: {
      eyebrow: "الوظائف",
      title: "سبع أدوات في خدمة التشخيص الترابي",
      intro: "النسخة التجريبية قيد الإنجاز. تُبيّن كل وظيفة بأمانة مدى تقدّمها.",
      inDevelopment: "قيد التطوير",
      available: "متاحة",
      mockup: "نموذج توضيحي — لا يتضمن أي معطيات حقيقية",
    },
    territories: {
      eyebrow: "مجالان ترابيان، أداة واحدة",
      title: "عاصمة حضرية، وإقليم بين المدينة والقرية",
      intro:
        "تتكيّف الأداة نفسها مع واقعين مختلفين دون تغيير سطر واحد من الشيفرة: الإعدادات وحدها تتغير.",
      unitsLabel: "وحدات التحليل",
      themesLabel: "الرهانات المتتبَّعة",
      items: [
        {
          code: "rabat",
          name: "الرباط",
          kind: "عاصمة حضرية بالكامل",
          region: "جهة الرباط سلا القنيطرة",
          units: "مقاطعات وجماعات تجمع الرباط سلا الصخيرات تمارة",
          themes: ["الولوج إلى الترامواي والحافلة", "المساحات الخضراء", "تجهيزات القرب"],
        },
        {
          code: "tetouan",
          name: "تطوان",
          kind: "إقليم حضري وقروي، بين الساحل والجبل",
          region: "جهة طنجة تطوان الحسيمة",
          units: "جماعات حضرية وقروية، ودواوير",
          themes: ["الطرق المعبدة والمسالك", "الماء الصالح للشرب والكهرباء", "النقل المدرسي"],
        },
      ],
    },
    how: {
      eyebrow: "كيف يشتغل",
      title: "من المعطيات إلى القرار، في ثلاث مراحل",
      steps: [
        {
          title: "المعطيات",
          text: "الإحصاء العام، OpenStreetMap، صور الأقمار الاصطناعية، وثائق التعمير، مساهمات المواطنين.",
        },
        {
          title: "الذكاء الاصطناعي",
          text: "يحسب المؤشرات، ويقارن الجماعات، ويلخّص آراء المواطنين، ويحرّر التقرير.",
        },
        {
          title: "القرار",
          text: "يراجع المختص في التعمير ويصادق، ويحسم صاحب القرار.",
        },
      ],
      motto: "الأداة تقترح، والمختص في التعمير يصادق.",
    },
    guarantees: {
      eyebrow: "ضماناتنا",
      title: "أداة جديرة بالثقة",
      items: [
        {
          title: "كل رقم موثّق المصدر",
          text: "المصدر والتاريخ ودرجة الموثوقية معروضة: رسمي، مفتوح، تقديري أو افتراضي.",
        },
        {
          title: "الذكاء الاصطناعي لا يختلق أي رقم",
          text: "يستشهد بوقائع متحقَّق منها. أي رقم غير معروف المصدر يوقف التقرير.",
        },
        {
          title: "حماية المعطيات الشخصية",
          text: "إخفاء منهجي للهوية قبل أي معالجة، طبقاً للقانون 09-08.",
        },
        {
          title: "ذكاء اصطناعي سيادي ممكن",
          text: "يمكن لـ«مجال» أن يشتغل بنموذج مستضاف في المغرب، دون أي خدمة أجنبية.",
        },
      ],
    },
    project: {
      eyebrow: "المشروع",
      title: "مقاربة علمية",
      text: "صُمّم «مجال» تحت الإشراف العلمي لأستاذ مؤهل بالمدرسة الوطنية للهندسة المعمارية بتطوان، متخصص في التعمير والحكامة الحضرية والذكاء الترابي والتسويق الترابي.",
      role: "المرجع العلمي",
      affiliation: "أستاذ مؤهل، المدرسة الوطنية للهندسة المعمارية بتطوان",
      photo: "[الصورة]",
      contact: "اتصلوا بنا",
      contactPending: "عنوان الاتصال في انتظار الإدراج",
    },
    footer: {
      demo: "نسخة تجريبية — معطيات للعرض",
      legal: "الإشعارات القانونية: [في انتظار الإدراج]",
      map: "خلفية الخريطة: Natural Earth (ملك عام)",
      rights: "© 2026 مجال",
      tagline: "مساعد ذكي في الذكاء الترابي",
    },
  },
};
