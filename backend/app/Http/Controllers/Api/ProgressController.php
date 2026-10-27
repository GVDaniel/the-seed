<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Validator;

class ProgressController extends Controller
{
    /**
     * Recibe progreso del cliente Godot (demo sin auth).
     * Persistencia durable se añadirá con migración + modelo PlayerProgress.
     */
    public function sync(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'player_name' => ['sometimes', 'string', 'max:64'],
            'completed_lessons' => ['sometimes', 'array'],
            'completed_lessons.*' => ['string', 'max:128'],
            'solved_puzzles' => ['sometimes', 'array'],
            'solved_puzzles.*' => ['string', 'max:128'],
            'stars_earned' => ['sometimes', 'integer', 'min:0', 'max:100000'],
        ]);

        if ($validator->fails()) {
            return response()->json([
                'message' => 'Payload inválido',
                'errors' => $validator->errors(),
            ], 422);
        }

        $payload = $validator->validated();
        Log::info('the-seed.progress.sync', $payload);

        return response()->json([
            'status' => 'synced',
            'received' => $payload,
        ]);
    }
}
