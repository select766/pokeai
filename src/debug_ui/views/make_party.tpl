<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
<script src="/js_enum/PokeType"></script>
<script src="/js_enum/Dexno"></script>
<script src="/js_enum/MoveID"></script>
<script src="/js_enum/PokeNVCondition"></script>
<script src="/static/js/make_party.js"></script>
<title>make party</title>
</head>
<body>
<form method="POST">
    <table>
        <tr><td>Dexno</td><td><select name="dexno"></select></td></tr>
        <tr><td>PokeType</td><td><select name="poke_type1" class="poke_type"></select><select name="poke_type2" class="poke_type"></td></tr>
        <tr><td>Moves</td><td>
            <select name="move"></select>
            <select name="move"></select>
            <select name="move"></select>
            <select name="move"></select>
            </td>
        </tr>
        <tr><td></td><td>
            HP<input type="text" name="max_hp" value="100" size="3">
            A<input type="text" name="st_a" value="100" size="3">
            B<input type="text" name="st_b" value="100" size="3">
            C<input type="text" name="st_c" value="100" size="3">
            S<input type="text" name="st_s" value="100" size="3">
            BaseS<input type="text" name="base_s" value="100" size="3">
            Level<input type="text" name="level" value="100" size="3"></td></tr>
    </table>

    <button type="submit" id="submit">Submit</button>
</form>
</body>
</html>