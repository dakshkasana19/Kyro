import * as z from "zod";

export const intakeFormSchema = z.object({
  // Demographics
  firstName: z.string().min(2, "First name is too short"),
  lastName: z.string().min(2, "Last name is too short"),
  dob: z.string().nonempty("Date of birth is required"),
  phone: z.string().min(10, "Phone number is invalid"),
  address: z.string().min(5, "Address is too short"),

  // Vitals
  height: z.coerce.number().positive("Height must be positive"),
  weight: z.coerce.number().positive("Weight must be positive"),
  bloodPressure: z.string().regex(/^\d{2,3}\/\d{2,3}$/, "Format: 120/80").nullable().optional(),
  temperature: z.coerce.number().min(90).max(110).nullable().optional(),

  // Symptoms
  chiefComplaint: z.string().min(10, "Please provide more detail about the complaint"),
  painLevel: z.coerce.number().min(0).max(10),
  symptomsDuration: z.string().nonempty("Duration is required"),

  // Medical History
  allergies: z.string().optional(),
  pastSurgeries: z.string().optional(),
  familyHistory: z.string().optional(),
  currentlyTakingMedications: z.boolean().default(false),
  medicationsSummary: z.string().optional()
});

export type IntakeFormValues = z.infer<typeof intakeFormSchema>;

export const stepFields = [
  ["firstName", "lastName", "dob", "phone", "address"],
  ["height", "weight", "bloodPressure", "temperature"],
  ["chiefComplaint", "painLevel", "symptomsDuration"],
  ["allergies", "pastSurgeries", "familyHistory", "currentlyTakingMedications", "medicationsSummary"]
];
