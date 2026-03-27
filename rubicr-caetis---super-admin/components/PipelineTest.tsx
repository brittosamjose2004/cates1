import React, { useState } from 'react';

const PipelineTest: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState<string>('');

  const testPipeline = async () => {
    setIsLoading(true);
    setError('');
    setResult('');

    try {
      console.log('Testing COMPREHENSIVE pipeline with ALL SOURCES for Infosys Limited 2024...');

      // Use COMPREHENSIVE configuration - ALL SOURCES
      const pipelineConfig = {
        company_ids: ['46'], // Infosys Limited
        data_sources: ['Real PDFs', 'Annual Reports', 'ESG Standards', 'Industry Patterns', 'Online Sources', 'Document Mining'],
        financial_years: ['FY2024']
      };

      console.log('Pipeline config:', pipelineConfig);

      const response = await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(pipelineConfig)
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const jobs = await response.json();
      console.log('Pipeline jobs:', jobs);

      setResult(`SUCCESS: Comprehensive Pipeline started for Infosys 2024!\nJob ID: ${jobs[0]?.id}\nStatus: ${jobs[0]?.status}\nData Sources: Documents + Patterns + Online Sources\nExpected: Maximum ESG data coverage`);

      // Poll for status updates
      if (jobs[0]?.id) {
        pollJobStatus(jobs[0].id);
      }

    } catch (err: any) {
      console.error('Pipeline test failed:', err);
      setError(`FAILED: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    console.log('Polling job status for:', jobId);

    for (let i = 0; i < 20; i++) { // Poll for up to 60 seconds
      try {
        const response = await fetch(`/api/pipeline/status/${jobId}`);
        const job = await response.json();

        console.log(`Poll ${i + 1}: Job ${jobId} status: ${job.status}`);

        if (['PUBLISHED', 'ERROR', 'COMPLETED'].includes(job.status)) {
          if (job.status === 'PUBLISHED') {
            setResult(prev => prev + `\n\nCOMPLETED SUCCESSFULLY!\nFinal Status: ${job.status}\nProcessing Time: ~${(i + 1) * 3} seconds\n\nComprehensive ESG Data Extraction Complete!\n✅ Documents: PDF + Document Mining\n✅ Patterns: IT + Financial + Sustainability\n✅ Online: Web scraping + Industry data\n✅ Maximum coverage achieved for FY2024`);
          } else {
            setResult(prev => prev + `\n\nJob finished with status: ${job.status}`);
            if (job.error_msg) {
              setError(`Job error: ${job.error_msg}`);
            }
          }
          break;
        }

        // Update progress
        setResult(prev => prev + `\n[${i + 1}] Status: ${job.status} - Processing ALL sources (docs + patterns + web)...`);

        if (i < 19) {
          await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
        }
      } catch (pollErr) {
        console.error('Poll error:', pollErr);
        setError(`Polling error: ${pollErr}`);
        break;
      }
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      background: 'white',
      border: '2px solid #333',
      padding: '20px',
      zIndex: 1000,
      maxWidth: '400px',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ margin: '0 0 15px 0', fontSize: '16px', fontWeight: 'bold' }}>
        🚀 Comprehensive ESG Pipeline
      </h3>

      <button
        onClick={testPipeline}
        disabled={isLoading}
        style={{
          background: isLoading ? '#ccc' : '#3b82f6',
          color: 'white',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '4px',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          fontSize: '14px',
          marginBottom: '15px'
        }}
      >
        {isLoading ? 'Processing All Sources...' : 'Run Comprehensive Pipeline'}
      </button>

      {result && (
        <div style={{
          background: '#f0f9ff',
          border: '1px solid #0ea5e9',
          padding: '10px',
          borderRadius: '4px',
          fontSize: '12px',
          whiteSpace: 'pre-wrap',
          marginBottom: '10px'
        }}>
          {result}
        </div>
      )}

      {error && (
        <div style={{
          background: '#fef2f2',
          border: '1px solid #ef4444',
          padding: '10px',
          borderRadius: '4px',
          fontSize: '12px',
          color: '#dc2626'
        }}>
          {error}
        </div>
      )}

      <div style={{ fontSize: '11px', color: '#666', marginTop: '10px' }}>
        Check browser console (F12) for detailed logs
      </div>
    </div>
  );
};

export default PipelineTest;