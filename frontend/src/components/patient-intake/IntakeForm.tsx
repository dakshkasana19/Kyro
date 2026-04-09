"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronRight, ChevronLeft, Check, ClipboardPlus } from "lucide-react";

import * as z from "zod";
import { intakeFormSchema, IntakeFormValues, stepFields } from "@/lib/validations/intake";
import { Form } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

import { DemographicsStep } from "./DemographicsStep";
import { VitalsStep } from "./VitalsStep";
import { SymptomsStep } from "./SymptomsStep";
import { MedicalHistoryStep } from "./MedicalHistoryStep";

const steps = [
  { id: "Step 1", name: "Demographics", component: DemographicsStep },
  { id: "Step 2", name: "Vitals", component: VitalsStep },
  { id: "Step 3", name: "Symptoms", component: SymptomsStep },
  { id: "Step 4", name: "Medical History", component: MedicalHistoryStep },
];

export function IntakeForm() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const form = useForm<z.input<typeof intakeFormSchema>>({
    resolver: zodResolver(intakeFormSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      dob: "",
      phone: "",
      address: "",
      height: 0,
      weight: 0,
      bloodPressure: "",
      temperature: 0,
      chiefComplaint: "",
      painLevel: 0,
      symptomsDuration: "",
      allergies: "",
      pastSurgeries: "",
      familyHistory: "",
      currentlyTakingMedications: false,
      medicationsSummary: "",
    },
    mode: "onChange",
  });

  const processNext = async () => {
    const fields = stepFields[currentStep];
    // Trigger validation for current step fields
    const isValid = await form.trigger(fields as any);
    
    if (isValid) {
      if (currentStep < steps.length - 1) {
        setCurrentStep((step) => step + 1);
      } else {
        // Submit
        form.handleSubmit(onSubmit)();
      }
    }
  };

  const processPrev = () => {
    if (currentStep > 0) {
      setCurrentStep((step) => step - 1);
    }
  };

  const onSubmit = async (data: any) => {
    setIsSubmitting(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    console.log("Intake Form Submitted:", data);
    setIsSubmitting(false);
    setIsSuccess(true);
  };

  const CurrentStepComponent = steps[currentStep].component;
  const progressPercentage = ((currentStep + 1) / steps.length) * 100;

  if (isSuccess) {
    return (
      <Card className="w-full max-w-2xl mx-auto border-emerald-500/20 bg-emerald-950/20 shadow-2xl shadow-emerald-900/20 animate-in zoom-in-95 duration-500">
        <CardContent className="pt-10 pb-10 flex flex-col items-center justify-center text-center space-y-6">
          <div className="w-20 h-20 bg-gradient-to-tr from-emerald-400 to-cyan-500 rounded-full flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <Check className="w-10 h-10 text-white" />
          </div>
          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-white">Intake Complete</h2>
            <p className="text-slate-300">Your information has been successfully securely transmitted.</p>
          </div>
          <Button 
            className="mt-4 bg-emerald-600 hover:bg-emerald-500"
            onClick={() => {
              form.reset();
              setCurrentStep(0);
              setIsSuccess(false);
            }}
          >
            Start New Intake
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-2xl border-slate-800 bg-slate-900/60 backdrop-blur-xl">
      <CardHeader>
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-gradient-to-tr from-purple-500 to-blue-500 rounded-lg shadow-lg">
            <ClipboardPlus className="w-6 h-6 text-white" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold text-white">Patient Intake Form</CardTitle>
            <CardDescription className="text-slate-400">
              {steps[currentStep].name} (Step {currentStep + 1} of {steps.length})
            </CardDescription>
          </div>
        </div>
        <Progress value={progressPercentage} className="h-2 mt-4 bg-slate-800" />
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form onSubmit={(e) => e.preventDefault()} className="space-y-8">
            <div className="min-h-[300px]">
              <CurrentStepComponent />
            </div>
          </form>
        </Form>
      </CardContent>

      <CardFooter className="flex justify-between border-t border-slate-800 pt-6">
        <Button
          type="button"
          variant="outline"
          onClick={processPrev}
          disabled={currentStep === 0 || isSubmitting}
          className="border-slate-700 hover:bg-slate-800"
        >
          <ChevronLeft className="w-4 h-4 mr-2" /> Previous
        </Button>
        
        <Button
          type="button"
          onClick={processNext}
          disabled={isSubmitting}
          className="bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-400 hover:to-blue-500 border-0 shadow-lg shadow-blue-900/50"
        >
          {isSubmitting ? (
            "Submitting..."
          ) : currentStep === steps.length - 1 ? (
            <>Submit <Check className="w-4 h-4 ml-2" /></>
          ) : (
            <>Next <ChevronRight className="w-4 h-4 ml-2" /></>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
