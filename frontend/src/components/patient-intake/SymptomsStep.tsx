import { useFormContext } from "react-hook-form";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export function SymptomsStep() {
  const { control } = useFormContext();

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <FormField
        control={control}
        name="chiefComplaint"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Chief Complaint</FormLabel>
            <FormControl>
              <Textarea 
                placeholder="Please describe your primary reason for today's visit in detail..." 
                className="min-h-[100px] resize-y"
                {...field} 
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={control}
          name="painLevel"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Pain Level (0-10)</FormLabel>
              <FormControl>
                <Input type="number" min="0" max="10" placeholder="0" {...field} />
              </FormControl>
              <FormDescription>0 is no pain, 10 is severe pain.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={control}
          name="symptomsDuration"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Duration of Symptoms</FormLabel>
              <FormControl>
                <Input placeholder="e.g., 3 days, 2 weeks" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    </div>
  );
}
