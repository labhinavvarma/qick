"use client";
 
import type React from "react";
import { useState, useRef, useEffect } from "react";
import { PatientForm, type PatientFormValues } from "./components/PatientForm";
import { ProgressView } from "./components/ProgressView";
import { ResultsView, type AnalysisResult } from "./components/ResultsView";
import AgentService from "./api/AgentService";
 
type Stage = "form" | "processing" | "complete";
 
export const App: React.FC = () => {
  const [stage, setStage] = useState<Stage>("form");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [patient, setPatient] = useState<PatientFormValues>({
    firstName: "",
    lastName: "",
    dob: "",
    gender: "",
    zip: "",
    ssn: "",
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const sectionRef = useRef<HTMLDivElement | null>(null);
  
  useEffect(() => {
    if (stage === "processing" && sectionRef.current) {
      sectionRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [stage]);
 
  async function handleSubmit(values: PatientFormValues) {
    setPatient(values);
    setStage("processing");
    setIsProcessing(true);
 
    try {
      const payload: {
        first_name: string;
        last_name: string;
        ssn: string;
        date_of_birth: string;
        gender: "M" | "F";
        zip_code: string;
      } = {
        first_name: values.firstName.trim(),
        last_name: values.lastName.trim(),
        ssn: values.ssn.trim(),
        date_of_birth: values.dob,
        gender: values.gender === "Female" ? "F" : "M",
        zip_code: values.zip.trim(),
      };
 
      const apiResponse = await AgentService.runAnalysisSync(payload);
 
      if (!apiResponse.success || !apiResponse.data?.analysis_results) {
        throw new Error("Invalid response from analysis API");
      }
 
      const analysis = apiResponse.data.analysis_results;
 
      const transformedResult: AnalysisResult = {
        claimsData: analysis.deidentified_data.medical || [],
        claimsAnalysis: analysis.deidentified_data?.pharmacy || [],
        mcidClaims: [analysis.deidentified_data.mcid || {}],
 
        extractionSummary: {
          serviceCodeCount:
            analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
              ?.flatMap((claim: any) =>
                claim.claim_lines?.map((line: any) => line.hlth_srvc_cd).filter((code: string) => !!code)
              ).length || 0,
 
          ICD10CodeCount: Object.keys(
            analysis.structured_extractions?.medical?.code_meanings?.diagnosis_code_meanings || {}
          ).length,
 
          medicalRecordCount: analysis.structured_extractions?.medical?.extraction_summary?.total_hlth_srvc_records || 0,
 
          billingProviderCount:
            Array.from(
              new Set(
                analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
                  ?.map((claim: any) => claim.billg_prov_nm)
                  .filter((name: string) => !!name)
              )
            ).length || analysis.structured_extractions?.medical?.extraction_summary?.total_diagnosis_codes || 0,
        },
 
        pharmacySummary: {
          ndcCodeCount: Object.keys(
            analysis.structured_extractions?.pharmacy?.code_meanings?.ndc_code_meanings || {}
          ).length,
 
          medicationCount: Object.keys(
            analysis.structured_extractions?.pharmacy?.code_meanings?.medication_meanings || {}
          ).length,
 
          pharmacyRecordCount:
            analysis.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS?.length || 0,
          
          prescribingProviderCount: Array.from(
            new Set(
              analysis.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS
                ?.map((claim: any) => claim.prscrbg_prov_nm)
                .filter((name: string) => !!name)
            )
          ).length || 0,
        },
 
        icd10Data: analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
            ?.filter((claim: any) => claim.diag_1_50_cd)
            .flatMap((claim: any) => {
              const codeMeanings = analysis.structured_extractions?.medical?.code_meanings?.diagnosis_code_meanings || {};
              const diagnosisCodes = claim.diag_1_50_cd.split(",");
              const results = [];
              for (const code of diagnosisCodes) {
                const trimmedCode = code.trim();
                const meaning = codeMeanings[trimmedCode];
                // Only add if meaning exists
                if (meaning) {
                  results.push({
                    code: trimmedCode,
                    meaning: meaning,
                    date: claim.clm_rcvd_dt || "",
                    provider: claim.billg_prov_nm || "",
                    zip: claim.billg_prov_zip_cd || "",
                  });
                }
              }
              return results;
            }) || [],
 
        serviceCodeData: analysis.api_outputs?.medical?.body?.MEDICAL_CLAIMS
           ?.flatMap((claim: any, claimIndex: number) => {
             const serviceMeanings = analysis.structured_extractions?.medical?.code_meanings?.service_code_meanings || {};
             const results = [];
             if (claim.claim_lines) {
               for (const line of claim.claim_lines) {
                 const trimmedCode = (line.hlth_srvc_cd || "").trim();
                 const serviceDescription = serviceMeanings[trimmedCode];
                 // Only add if description exists
                 if (serviceDescription) {
                   results.push({
                     serviceCode: trimmedCode,
                     serviceDescription: serviceDescription,
                     date: line.clm_line_srvc_end_dt || "",
                     path: `MEDICAL_CLAIMS[${claimIndex}].claim_lines[${line.clm_line_nbr || 0}]`
                   });
                 }
               }
             }
             return results;
           }) || [],
 
        ndcData: (() => {
           try {
             const ndcMeanings = analysis?.structured_extractions?.pharmacy?.code_meanings?.ndc_code_meanings || {};
             const claims = analysis?.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS || [];
 
             console.log('💊 NDC EXTRACTION - Claims:', claims.length, '| Dictionary:', Object.keys(ndcMeanings).length);
 
             if (!claims || claims.length === 0) return [];
 
             return claims.map((claim: any, index: number) => {
               const ndcCode = (claim?.ndc || "N/A").trim();
               const medName = (claim?.lbl_nm || "Unknown").trim();
 
               // Try to get description from NDC dictionary
               let description = ndcMeanings[ndcCode]
                              || ndcMeanings[ndcCode.replace(/-/g, '')] // Try without dashes
                              || "";
 
               // If no NDC description, just show medication name
               if (!description) {
                 description = medName ? `Medication: ${medName}` : "No description available";
               }
 
               return {
                 code: ndcCode,
                 medication: medName,
                 date: claim?.rx_filled_dt || "N/A",
                 description: description,
                 path: `PHARMACY_CLAIMS[${index}]`
               };
             });
           } catch (error) {
             console.error('❌ NDC extraction error:', error);
             return [];
           }
         })(),
 
        medicationData: (() => {
           try {
             // Try to get BOTH dictionaries
             const medicationMeanings = analysis?.structured_extractions?.pharmacy?.code_meanings?.medication_meanings || {};
             const ndcMeanings = analysis?.structured_extractions?.pharmacy?.code_meanings?.ndc_code_meanings || {};
             const claims = analysis?.api_outputs?.pharmacy?.body?.PHARMACY_CLAIMS || [];
 
             console.log('💊 MEDICATION EXTRACTION');
             console.log('  Claims:', claims.length);
             console.log('  Medication dictionary:', Object.keys(medicationMeanings).length);
             console.log('  NDC dictionary:', Object.keys(ndcMeanings).length);
 
             if (!claims || claims.length === 0) return [];
 
             return claims.map((claim: any, index: number) => {
               const medName = (claim?.lbl_nm || "Unknown Medication").trim();
               const ndcCode = (claim?.ndc || "").trim();
 
               let description = "";
 
               // METHOD 1: Try medication_meanings dictionary
               if (Object.keys(medicationMeanings).length > 0) {
                 description = medicationMeanings[medName]
                            || medicationMeanings[medName.toUpperCase()]
                            || medicationMeanings[medName.toLowerCase()]
                            || "";
 
                 // Try first word match (e.g., "LISINOPRIL" for "LISINOPRIL 10MG TAB")
                 if (!description && medName) {
                   const firstWord = medName.split(/\s+/)[0];
                   description = medicationMeanings[firstWord]
                              || medicationMeanings[firstWord.toUpperCase()]
                              || "";
                 }
               }
 
               // METHOD 2: If no medication description, try NDC dictionary
               if (!description && Object.keys(ndcMeanings).length > 0 && ndcCode) {
                 description = ndcMeanings[ndcCode]
                            || ndcMeanings[ndcCode.replace(/-/g, '')]
                            || "";
               }
 
               // METHOD 3: If still nothing, create generic description from medication name
               if (!description) {
                 // Parse medication name for common patterns
                 const genericName = medName.split(/\d+/)[0].trim(); // Get name before dosage
                 description = genericName ? `Medication: ${genericName}` : "Prescription medication";
               }
 
               return {
                 ndcCode: ndcCode || "N/A",
                 medication: medName,
                 fillDate: claim?.rx_filled_dt || "N/A",
                 description: description,
                 billingProvider: claim?.billg_prov_nm || "N/A",
                 prescribingProvider: claim?.prscrbg_prov_nm || "N/A",
                 path: `PHARMACY_CLAIMS[${index}]`
               };
             });
           } catch (error) {
             console.error('❌ Medication extraction error:', error);
             return [];
           }
         })(),
 
        entities: [
          { type: "Diabetes Status", value: analysis.entity_extraction?.diabetics || "Unknown" },
          { type: "Age", value: String(analysis.entity_extraction?.age || "unknown") },
          { type: "Age Group", value: analysis.entity_extraction?.age_group || "Unknown" },
          { type: "Smoking Status", value: analysis.entity_extraction?.smoking || "Unknown" },
          { type: "Alcohol Use", value: analysis.entity_extraction?.alcohol || "Unknown" },
          { type: "Blood Pressure", value: analysis.entity_extraction?.blood_pressure || "Unknown" },
        ],
        healthTrajectory: analysis.health_trajectory,
        heartRisk: {
          score: Math.round((analysis.heart_attack_prediction?.raw_risk_score || 0) * 100),
          level: analysis.heart_attack_prediction?.risk_category || "Unknown",
        },
      };
 
      setResult(transformedResult);
      setIsProcessing(false);
      setStage("complete");
    } catch (e) {
      console.error("Analysis failed:", e);
      setIsProcessing(false);
      setStage("form");
    }
  }
 
  function handleComplete() {
    setStage("complete");
    setShowResults(true);
  }
 
  function handleRunAgain() {
    setStage("form");
    setResult(null);
    setIsProcessing(false);
    setShowResults(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
 
  return (
    <div className="w-full">
      <main
        className={`relative w-full bg-cover bg-no-repeat bg-center transition-all duration-700`}
        style={{
          backgroundImage: "url('/bg-image.png')",
          height: stage === "form" ? "100vh" : "78vh",
        }}
      >
        {/* Header with Chatbot Button */}
        <div className="relative">
          <h1
            className="text-4xl font-extrabold text-center pt-8 relative bg-gradient-to-r from-blue-900 via-indigo-500 to-sky-300 bg-clip-text text-transparent"
            style={{
              fontFamily:
                'ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
            }}
          >
            <span className="shine-text">
              Deep Research Health Agent 3.0
            </span>

            <style>
              {`
        .shine-text {
          background-image: linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,0.9),
            transparent
          );
          background-repeat: no-repeat;
          background-size: 200% 100%;
          -webkit-background-clip: text;
          background-clip: text;
          animation: shine 5s ease-in-out infinite;
          display: inline-block;
        }
   
        @keyframes shine {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}
            </style>
          </h1>

          {/* Chatbot Button in Header */}
          <button
            onClick={() => window.open('/page', '_blank', 'noopener,noreferrer')}
            className="absolute top-8 right-8 flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105"
            aria-label="Open Medical Assistant"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span className="font-semibold">Medical Assistant</span>
          </button>
        </div>

        <div className="flex justify-end items-center h-full px-10">
          <PatientForm onSubmit={handleSubmit} initialValues={patient} />
        </div>
      </main>
 
      <section className="px-6 py-8" style={{ background: "#fff" }}>
        {stage === "processing" && <ProgressView isProcessing={isProcessing} onComplete={handleComplete} />}
        {stage === "complete" && result && <ResultsView result={result} onRunAgain={handleRunAgain} />}
      </section>

      {/* Floating Chatbot Button */}
      <button
        onClick={() => window.open('/page', '_blank', 'noopener,noreferrer')}
        className="fixed bottom-8 right-8 w-16 h-16 bg-blue-600 text-white rounded-full shadow-2xl hover:bg-blue-700 hover:scale-110 transition-all duration-300 z-50 flex items-center justify-center group"
        aria-label="Open Medical Assistant"
        title="Chat with Medical Assistant"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        {/* Tooltip on hover */}
        <span className="absolute right-full mr-3 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
          Medical Assistant
        </span>
      </button>
    </div>
  );
};
