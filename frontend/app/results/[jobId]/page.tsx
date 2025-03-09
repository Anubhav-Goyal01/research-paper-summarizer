'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import KeyConcepts from '../../../components/KeyConcepts';
import ProblemStatement from '../../../components/ProblemStatement';
import FullExplanation from '../../../components/FullExplanation';
import PseudoCode from '../../../components/PseudoCode';
import React from 'react';

export default function ResultsPage({ params }: { params: { jobId: string } }) {
  const { jobId } = params;
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/status/${jobId}`);
        const responseData = await response.json();
        setData(responseData);
      } catch (error) {
        console.error('Error fetching paper analysis:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [jobId]);

  if (loading) {
    return (
      <main className="min-h-screen flex flex-col">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-primary-600">Analysis Results</h1>
          </div>
        </header>
        <div className="flex-grow flex items-center justify-center">
          <div className="animate-pulse flex flex-col items-center">
            <div className="h-12 w-12 rounded-full bg-primary-200 mb-4"></div>
            <div className="h-4 w-48 bg-primary-200 rounded mb-2"></div>
            <div className="h-3 w-36 bg-primary-100 rounded"></div>
          </div>
        </div>
      </main>
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
