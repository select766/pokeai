<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script src="/js_enum/PokeType"></script>
<script src="/js_enum/Dexno"></script>
<script src="/js_enum/MoveID"></script>
<script src="/static/js/battle.js"></script>
<link rel="stylesheet" href="/static/css/ui.css" type="text/css" />
<title>battle</title>
</head>
<body>
<form>
    <table>
        <tr>
            % for player in [0, 1]:
            <td class="player{{player}}">
                Player {{player}}
                <table class="fighting_poke">
                    <tr><td>Dexno</td><td class="dexno"></td></tr>
                    <tr><td>HP</td><td class="hp"></td></tr>
                    <tr><td>Moves</td><td class="moves"></td></tr>
                    <tr><td>NVCondition</td><td class="nv_condition"></td></tr>
                    <tr><td>Condition</td><td class="condition"></td></tr>
                    <tr><td>Rank</td><td class="rank"></td></tr>
                </table>
                <div class="party_pokes">
                </div>
            </td>
            % end
        </tr>
    </table>
    <div>
        <button type="button" name="do_step">Step</button><span class="phase"></span>
    </div>
    <div>
        <textarea name="log" style="width: 1000px; height: 400px;"></textarea>
    </div>
</form>
</body>
</html>