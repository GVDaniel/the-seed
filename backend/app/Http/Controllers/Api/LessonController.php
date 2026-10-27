<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;

class LessonController extends Controller
{
    /**
     * Catálogo mínimo alineado con game/assets/data/astronomy.
     * Más adelante puede leerse de BD o del filesystem compartido.
     */
    public function index(): JsonResponse
    {
        return response()->json([
            'data' => [
                [
                    'id' => 'demo_sol_overview',
                    'title' => 'Nuestro Sol',
                    'age_band' => '10-14',
                    'source' => 'seed',
                ],
            ],
        ]);
    }
}
