'use client';

import React from 'react';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card } from '../../../components/Card';
import KeyConcepts from '../../../components/KeyConcepts';
import ProblemStatement from '../../../components/ProblemStatement';
import FullExplanation from '../../../components/FullExplanation';
import PseudoCode from '../../../components/PseudoCode';
import { Loader } from '../../../components/Loader';

export default function ResultsPage({ params }: { params: { jobId: string } }) {
  const { jobId } = params;
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>('Initializing analysis...');

  useEffect(() => {
    let pollingInterval: NodeJS.Timeout;
    let progressCounter = 0;
    
    const fetchData = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/status/${jobId}`);
        
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        
        const responseData = await response.json();
        
        if (responseData.status === 'completed') {
          setData(responseData);
          setLoading(false);
          clearInterval(pollingInterval);
        } 
        else if (responseData.status === 'in_progress') {
          setStatusMessage(`Analyzing paper: ${responseData.filename || 'your document'}`);
          
          if (progressCounter < 90) {
            progressCounter += Math.floor(Math.random() * 5) + 1;
            setProgress(Math.min(progressCounter, 90));
          }
        } 
        else if (responseData.status === 'failed') {
          setError(`Analysis failed: ${responseData.error || 'Unknown error'}`);
          setLoading(false);
          clearInterval(pollingInterval);
        }
      } catch (error) {
        console.error('Error fetching paper analysis:', error);
        setError('Failed to connect to analysis server. Please try again later.');
        setLoading(false);
        clearInterval(pollingInterval);
      }
    };

    fetchData();
    pollingInterval = setInterval(fetchData, 3000); 

    const progressInterval = setInterval(() => {
      if (progressCounter < 90) {
        progressCounter += 1;
        setProgress(progressCounter);
      }
    }, 500);

    return () => {
      clearInterval(pollingInterval);
      clearInterval(progressInterval);
    };
  }, [jobId]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-5xl mx-auto">
          <div className="flex justify-between items-center mb-6">
            <Link 
              href="/"
              className="text-sm font-medium text-primary-600 hover:text-primary-500 transition-colors"
            >
              &larr; Back to Home
            </Link>
            <span className="text-sm text-neutral-500">Job ID: {jobId}</span>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-8">
            <Loader message={statusMessage} />
            
            <div className="mt-8 max-w-md mx-auto">
              <div className="w-full bg-neutral-200 rounded-full h-2.5">
                <div 
                  className="bg-primary-600 h-2.5 rounded-full transition-all duration-500" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <div className="flex justify-between mt-2 text-xs text-neutral-500">
                <span>Uploading</span>
                <span>Analyzing</span>
                <span>Formatting</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data || !data.result) {
    return (
      <main className="min-h-screen flex flex-col">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-primary-600">Analysis Results</h1>
          </div>
        </header>
        <div className="flex-grow flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-4 text-neutral-700">Analysis not found</h2>
            <p className="mb-6 text-neutral-600">The requested analysis could not be found or has not been completed yet.</p>
            <Link href="/upload"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
              Try another paper
            </Link>
          </div>
        </div>
      </main>
    );
  }

  const { metadata, key_concepts, problem_statement, full_explanation, pseudo_code } = data.result;

  return (
    <main className="min-h-screen flex flex-col">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <h1 className="text-3xl font-bold text-primary-600">Paper Analysis</h1>
            <Link href="/upload" className="mt-2 md:mt-0 text-sm text-primary-600 hover:text-primary-500">
              Analyze another paper
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 flex-grow">
        <div className="mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-neutral-200">
            <h2 className="text-2xl font-bold text-neutral-800 mb-2">{metadata.title}</h2>
            <p className="text-neutral-600">{metadata.authors}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <KeyConcepts data={key_concepts} />
          <ProblemStatement data={problem_statement} />
        </div>

        <div className="mb-8">
          <FullExplanation data={full_explanation} />
        </div>

        <div className="mb-8">
          <PseudoCode data={pseudo_code} />
        </div>
      </div>
    </main>
  );
}
