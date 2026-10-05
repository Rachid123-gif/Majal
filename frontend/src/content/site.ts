/**
 * Informations du projet à compléter par le porteur du projet.
 * Remplacez les valeurs entre crochets, enregistrez : la page se met à jour toute seule.
 */
export const site = {
  /** Nom affiché du référent scientifique. */
  professorName: "[Nom du professeur]",
  /** Photo du référent : placez le fichier dans frontend/public/ et indiquez son nom, par exemple "/professeur.jpg". */
  professorPhoto: null as string | null,
  /** Adresse e-mail du bouton « Nous contacter ». */
  contactEmail: "[email]",
};

export const isPlaceholder = (value: string) => value.startsWith("[") && value.endsWith("]");
