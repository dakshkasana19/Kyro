import { useFormContext } from "react-hook-form";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export function MedicalHistoryStep() {
  const { control, watch } = useFormContext();
  const currentlyTakingMedications = watch("currentlyTakingMedications");

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <FormField
        control={control}
        name="allergies"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Known Allergies</FormLabel>
            <FormControl>
              <Input placeholder="e.g., Penicillin, Peanuts (or 'None')" {...field} value={field.value || ''} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={control}
        name="pastSurgeries"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Past Surgeries</FormLabel>
            <FormControl>
              <Textarea 
                placeholder="List any past surgeries and dates (or 'None')" 
                className="resize-y"
                {...field} 
                value={field.value || ''}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={control}
        name="familyHistory"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Relevant Family Medical History</FormLabel>
            <FormControl>
              <Textarea 
                placeholder="e.g., Heart disease, Diabetes..." 
                className="resize-y"
                {...field} 
                value={field.value || ''}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={control}
        name="currentlyTakingMedications"
        render={({ field }) => (
          <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4 shadow-sm border-slate-700 bg-slate-800/20">
            <FormControl>
              <input 
                type="checkbox"
                className="mt-1 h-4 w-4 shrink-0 rounded-sm border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none bg-slate-900 border"
                checked={field.value}
                onChange={field.onChange}
              />
            </FormControl>
            <div className="space-y-1 leading-none">
              <FormLabel>Currently Taking Medications?</FormLabel>
              <FormDescription>
                Check this box if you are currently taking any prescription or over-the-counter medications.
              </FormDescription>
            </div>
          </FormItem>
        )}
      />
      
      {currentlyTakingMedications && (
        <FormField
          control={control}
          name="medicationsSummary"
          render={({ field }) => (
            <FormItem className="animate-in fade-in zoom-in-95 duration-200">
              <FormLabel>List Medications and Dosages</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="e.g., Lisinopril 10mg daily..." 
                  className="resize-y"
                  {...field} 
                  value={field.value || ''}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      )}
    </div>
  );
}
